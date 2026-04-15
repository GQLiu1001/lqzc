"""提供与domainsubworkflow相关的实现。"""

from __future__ import annotations

import json
import logging
import time
from typing import Awaitable, Callable, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.memory.memory_store import MemoryStore
from app.observability.metrics import metrics
from app.schemas.task import TaskStatus
from app.tools.approval_tools.approval_tool import ApprovalTool
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools
from app.tools.rag_tools.retriever_tool import RetrieverTool
from app.workflows.shared_nodes import format_retrieval_context, format_tool_context


logger = logging.getLogger(__name__)


class DomainWorkflowState(TypedDict, total=False):
    """业务子工作流共享的状态对象。

    客服和仓储虽然是两个不同子图，但它们执行步骤很像：
    检索 -> 调工具 -> 过风控 -> 生成回答。
    所以这里抽出一份通用状态结构，避免两套流程各写一遍。
    """
    session_id: str
    user_id: str | None
    tenant_id: str | None
    context: dict
    message: str
    task_id: str
    status: str
    current_agent: str
    route_reason: str
    route_source: str
    route_confidence: float | None
    risk_level: str
    requires_approval: bool
    retrieval_domain: str
    collection_name: str
    retrieval_hits: list[dict]
    tool_trace: list[dict]
    answer: str
    evidence: list[dict]
    error: str


AnswerGenerator = Callable[[str, str], Awaitable[str]]


class DomainSubWorkflow:
    """业务域子工作流的通用骨架。

    这个类是个“模板”：
    - 客服子流程复用它
    - 仓储子流程也复用它

    真正不同的部分只有“最后由哪个 Agent 负责生成答案”，
    所以用 `answer_generator` 作为可注入函数传进来。
    """
    def __init__(
        self,
        *,
        workflow_name: str,
        memory: MemoryStore,
        retriever_tool: RetrieverTool,
        business_tools: LQZCBusinessTools,
        approval_tool: ApprovalTool,
        answer_generator: AnswerGenerator,
    ) -> None:
        """初始化domainSUB工作流，把运行时依赖和基础状态准备好。"""
        self.workflow_name = workflow_name
        self.memory = memory
        self.retriever_tool = retriever_tool
        self.business_tools = business_tools
        self.approval_tool = approval_tool
        self.answer_generator = answer_generator
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建子工作流状态图。

        这条链路是整个 AI 回答生成的核心主干：
        1. `retrieve_context` 去知识库找证据。
        2. `invoke_tools` 去业务系统查订单、查库存或生成审批草案。
        3. `risk_gate` 判断是否需要人工审批。
        4. 不需要审批就 `draft_answer`，需要就 `wait_approval`。
        """
        graph = StateGraph(DomainWorkflowState)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("invoke_tools", self._invoke_tools)
        graph.add_node("risk_gate", self._risk_gate)
        graph.add_node("wait_approval", self._wait_approval)
        graph.add_node("draft_answer", self._draft_answer)

        graph.add_edge(START, "retrieve_context")
        graph.add_edge("retrieve_context", "invoke_tools")
        graph.add_edge("invoke_tools", "risk_gate")
        graph.add_conditional_edges(
            "risk_gate",
            self._risk_branch,
            {
                "WAITING_APPROVAL": "wait_approval",
                "CONTINUE": "draft_answer",
            },
        )
        graph.add_edge("wait_approval", END)
        graph.add_edge("draft_answer", END)
        return graph.compile(checkpointer=MemorySaver())

    async def run(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """执行子工作流。

        这里调用的是 LangGraph 的 `ainvoke`。
        `thread_id=task_id` 的意义是：让这条工作流执行和当前 task 绑定，
        便于后续做 checkpoint、恢复和追踪。
        """
        task_id = str(state["task_id"])
        graph_state = await self.graph.ainvoke(
            state,
            config={"configurable": {"thread_id": task_id}},
        )
        return graph_state

    async def _retrieve_context(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """执行 RAG 检索，先给模型补业务证据。

        大模型本身不一定知道你们公司的订单规则、库存 SOP、售后政策，
        所以这里会先去向量库里查相关资料，再把命中的文本证据放进状态里。
        后面生成答案时，这些证据会被拼进 prompt。
        """
        task_id = state["task_id"]
        node_name = "retrieve_context"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        retrieval_domain = state.get("retrieval_domain") or state.get("current_agent") or "customer_service"
        from_status = str(state.get("status") or TaskStatus.ROUTED.value)
        to_status = TaskStatus.RETRIEVING.value
        metrics.record_task_transition(
                from_status=from_status,
                to_status=to_status,
                agent=str(state.get("current_agent") or "unknown"),
            )
        self.memory.task.update(task_id=task_id, status=TaskStatus.RETRIEVING)
        try:
            # `collection_name` 表示命中的知识库集合，`hits` 是检索到的片段列表。
            collection_name, hits = self.retriever_tool.retrieve(
                query=state["message"],
                domain=str(retrieval_domain),
                tenant_id=state.get("tenant_id"),
                top_k=settings.rag_top_k,
            )
            self.memory.mysql.insert_retrieval_trace(
                task_id=task_id,
                query_text=state["message"],
                domain=str(retrieval_domain),
                collection_name=collection_name,
                hits=len(hits),
            )
            metrics.observe_retrieval(
                workflow=self.workflow_name,
                domain=str(retrieval_domain),
                collection=collection_name,
                hits=len(hits),
            )
            logger.info(
                "subworkflow.retrieve name=%s task_id=%s domain=%s collection=%s hits=%s",
                self.workflow_name,
                task_id,
                retrieval_domain,
                collection_name,
                len(hits),
            )
            success = True
            return {
                **state,
                "status": TaskStatus.RETRIEVING.value,
                "collection_name": collection_name,
                "retrieval_hits": hits,
                # 同一份检索结果会被整理成更标准的 evidence 结构，供 API 直接返回前端。
                "evidence": [
                    {
                        "source": str(item.get("source", collection_name)),
                        "content": str(item.get("content", "")),
                        "score": float(item.get("score", 0.0)),
                        "metadata": item.get("metadata", {}) or {},
                    }
                    for item in hits
                ],
            }
        finally:
            metrics.observe_node_duration(
                workflow=self.workflow_name,
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def _invoke_tools(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """根据业务域和消息内容调用业务工具。

        检索解决的是“知识问答”，工具解决的是“实时业务数据”。
        比如：
        - 检索能回答退款规则是什么
        - 工具能回答某个订单当前状态是什么

        这一步会把工具执行结果都记进 `tool_trace`，方便最终拼上下文和排障。
        """
        task_id = state["task_id"]
        node_name = "invoke_tools"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        from_status = str(state.get("status") or TaskStatus.RETRIEVING.value)
        to_status = TaskStatus.TOOL_RUNNING.value
        metrics.record_task_transition(
                from_status=from_status,
                to_status=to_status,
                agent=str(state.get("current_agent") or "unknown"),
            )
        self.memory.task.update(task_id=task_id, status=TaskStatus.TOOL_RUNNING)
        trace = list(state.get("tool_trace", []))
        try:
            try:
                # 这里不是让 LLM 自由调用工具，而是由工具层根据消息抽取结构化参数。
                tool_results = await self.business_tools.run_by_route(
                    route_label=state.get("current_agent", ""),
                    message=state["message"],
                )
            except Exception as exc:
                logger.warning(
                    "subworkflow.tools.failed name=%s task_id=%s agent=%s error=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_agent"),
                    exc,
                )
                trace.append(
                    {
                        "tool_name": "business_tool_dispatch",
                        "arguments": {
                            "message": state["message"],
                            "agent": state.get("current_agent"),
                        },
                        "result_preview": str(exc)[:500],
                        "status": "FAILED",
                    }
                )
                self.memory.mysql.insert_tool_trace(
                    task_id=task_id,
                    tool_name="business_tool_dispatch",
                    arguments={
                        "message": state["message"],
                        "agent": state.get("current_agent"),
                    },
                    result_preview=str(exc),
                    result={"error": str(exc)},
                    status="FAILED",
                )
                success = True
                return {**state, "status": TaskStatus.TOOL_RUNNING.value, "tool_trace": trace}

            if not tool_results:
                logger.info(
                    "subworkflow.tools.none name=%s task_id=%s agent=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_agent"),
                )
                success = True
                return {**state, "status": TaskStatus.TOOL_RUNNING.value, "tool_trace": trace}

            # 统一把不同格式的工具结果规范成 trace 结构。
            for item in tool_results:
                if isinstance(item, tuple) and len(item) == 2:
                    tool_name = str(item[0])
                    result = item[1]
                    arguments = {
                        "message": state["message"],
                        "agent": state.get("current_agent"),
                    }
                    tool_status = "SUCCESS"
                elif isinstance(item, dict):
                    tool_name = str(item.get("tool_name", "unknown_tool"))
                    result = item.get("result")
                    arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
                    tool_status = str(item.get("status", "SUCCESS"))
                else:
                    tool_name = "unknown_tool"
                    result = item
                    arguments = {
                        "message": state["message"],
                        "agent": state.get("current_agent"),
                    }
                    tool_status = "SUCCESS"

                if isinstance(result, (dict, list)):
                    try:
                        result_preview = json.dumps(result, ensure_ascii=False)
                    except Exception:
                        result_preview = str(result)
                else:
                    result_preview = str(result)
                if tool_status.startswith("SUCCESS"):
                    logger.info(
                        "subworkflow.tools.result name=%s task_id=%s tool=%s status=%s preview_len=%s",
                        self.workflow_name,
                        task_id,
                        tool_name,
                        tool_status,
                        len(result_preview),
                    )
                else:
                    logger.warning(
                        "subworkflow.tools.result name=%s task_id=%s tool=%s status=%s preview_len=%s",
                        self.workflow_name,
                        task_id,
                        tool_name,
                        tool_status,
                        len(result_preview),
                    )
                trace.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result_preview": result_preview[:500],
                        "status": tool_status,
                    }
                )
                self.memory.mysql.insert_tool_trace(
                    task_id=task_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    result_preview=result_preview,
                    result=result,
                    status=tool_status[:20],
                )
            success = True
            return {**state, "status": TaskStatus.TOOL_RUNNING.value, "tool_trace": trace}
        finally:
            metrics.observe_node_duration(
                workflow=self.workflow_name,
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def _risk_gate(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """风控闸门，决定这次请求是继续还是挂起等待审批。

        关键思想：
        - “查询类”请求通常可以直接继续。
        - “执行类”或高风险请求不应该让 AI 直接落库或改业务数据。
        - 所以先生成审批单，再等待人工确认。
        """
        task_id = state["task_id"]
        node_name = "risk_gate"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        try:
            if settings.enable_approval and state.get("requires_approval"):
                metrics.record_task_transition(
                    from_status=str(state.get("status") or TaskStatus.TOOL_RUNNING.value),
                    to_status=TaskStatus.WAITING_APPROVAL.value,
                    agent=str(state.get("current_agent") or "unknown"),
                )
                # 这里先登记一个待审批动作，真正执行危险动作要等审批通过后再做。
                self.approval_tool.request(task_id=task_id, approval_action="approve")
                self.memory.task.update(task_id=task_id, status=TaskStatus.WAITING_APPROVAL)
                logger.info(
                    "subworkflow.risk.waiting_approval name=%s task_id=%s agent=%s risk=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_agent"),
                    state.get("risk_level"),
                )
                success = True
                return {**state, "status": TaskStatus.WAITING_APPROVAL.value}

            logger.info(
                "subworkflow.risk.pass name=%s task_id=%s agent=%s",
                self.workflow_name,
                task_id,
                state.get("current_agent"),
            )
            success = True
            return state
        finally:
            metrics.observe_node_duration(
                workflow=self.workflow_name,
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    def _risk_branch(self, state: DomainWorkflowState) -> str:
        """根据当前状态决定从 risk_gate 走向哪个分支。"""
        if state.get("status") == TaskStatus.WAITING_APPROVAL.value:
            return "WAITING_APPROVAL"
        return "CONTINUE"

    async def _wait_approval(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """在需要审批时返回一个明确提示，而不是直接执行业务动作。"""
        task_id = state["task_id"]
        node_name = "wait_approval"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        try:
            logger.info("subworkflow.wait_approval name=%s task_id=%s", self.workflow_name, task_id)
            answer = "该请求涉及高风险动作，已进入审批流程。请调用 /tasks/approve 完成审批后继续。"
            success = True
            return {**state, "answer": answer}
        finally:
            metrics.observe_node_duration(
                workflow=self.workflow_name,
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def _draft_answer(self, state: DomainWorkflowState) -> DomainWorkflowState:
        """把检索证据和工具结果拼成上下文，再交给具体 Agent 生成答案。

        这一层本身不关心“你是客服 Agent 还是仓储 Agent”，
        它只负责把上下文整理好，再调用注入进来的 `answer_generator`。
        """
        task_id = state["task_id"]
        node_name = "draft_answer"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        retrieval_context = format_retrieval_context(state.get("retrieval_hits", []))
        tool_context = format_tool_context(state.get("tool_trace", []))
        # 检索上下文 + 工具上下文 = 给大模型看的“事实材料”。
        final_context = "\n".join(part for part in (retrieval_context, tool_context) if part.strip())
        logger.info(
            "subworkflow.draft name=%s task_id=%s agent=%s retrieval_hits=%s tools=%s context_len=%s",
            self.workflow_name,
            task_id,
            state.get("current_agent"),
            len(state.get("retrieval_hits", [])),
            len(state.get("tool_trace", [])),
            len(final_context),
        )

        try:
            answer = await self.answer_generator(
                state["message"],
                final_context,
            )
            success = True
            return {**state, "answer": answer}
        finally:
            metrics.observe_node_duration(
                workflow=self.workflow_name,
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )
