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
    session_id: str
    user_id: str | None
    tenant_id: str | None
    context: dict
    message: str
    task_id: str
    status: str
    current_agent: str
    current_skill: str
    route_reason: str
    route_source: str
    route_confidence: float | None
    risk_level: str
    requires_approval: bool
    retrieval_domain: str
    skill_instruction: str
    response_contract: str
    tool_hints: list[str]
    collection_name: str
    retrieval_hits: list[dict]
    tool_trace: list[dict]
    answer: str
    evidence: list[dict]
    error: str


AnswerGenerator = Callable[[str, str, str, str], Awaitable[str]]


class DomainSubWorkflow:
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
        self.workflow_name = workflow_name
        self.memory = memory
        self.retriever_tool = retriever_tool
        self.business_tools = business_tools
        self.approval_tool = approval_tool
        self.answer_generator = answer_generator
        self.graph = self._build_graph()

    def _build_graph(self):
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
        task_id = str(state["task_id"])
        graph_state = await self.graph.ainvoke(
            state,
            config={"configurable": {"thread_id": task_id}},
        )
        return graph_state

    async def _retrieve_context(self, state: DomainWorkflowState) -> DomainWorkflowState:
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
            skill=str(state.get("current_skill") or "unknown"),
        )
        self.memory.task.update(task_id=task_id, status=TaskStatus.RETRIEVING)
        try:
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
            skill=str(state.get("current_skill") or "unknown"),
        )
        self.memory.task.update(task_id=task_id, status=TaskStatus.TOOL_RUNNING)
        trace = list(state.get("tool_trace", []))
        try:
            try:
                tool_results = await self.business_tools.run_by_skill(
                    skill_name=state.get("current_skill", ""),
                    message=state["message"],
                    tool_hints=tuple(state.get("tool_hints", [])),
                )
            except Exception as exc:
                logger.warning(
                    "subworkflow.tools.failed name=%s task_id=%s skill=%s error=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_skill"),
                    exc,
                )
                trace.append(
                    {
                        "tool_name": "skill_tool_dispatch",
                        "arguments": {
                            "message": state["message"],
                            "skill": state.get("current_skill"),
                        },
                        "result_preview": str(exc)[:500],
                        "status": "FAILED",
                    }
                )
                self.memory.mysql.insert_tool_trace(
                    task_id=task_id,
                    tool_name="skill_tool_dispatch",
                    arguments={
                        "message": state["message"],
                        "skill": state.get("current_skill"),
                    },
                    result_preview=str(exc),
                    result={"error": str(exc)},
                    status="FAILED",
                )
                success = True
                return {**state, "status": TaskStatus.TOOL_RUNNING.value, "tool_trace": trace}

            if not tool_results:
                logger.info(
                    "subworkflow.tools.none name=%s task_id=%s skill=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_skill"),
                )
                success = True
                return {**state, "status": TaskStatus.TOOL_RUNNING.value, "tool_trace": trace}

            for item in tool_results:
                if isinstance(item, tuple) and len(item) == 2:
                    tool_name = str(item[0])
                    result = item[1]
                    arguments = {
                        "message": state["message"],
                        "skill": state.get("current_skill"),
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
                        "skill": state.get("current_skill"),
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
                    skill=str(state.get("current_skill") or "unknown"),
                )
                self.approval_tool.request(task_id=task_id, approval_action="approve")
                self.memory.task.update(task_id=task_id, status=TaskStatus.WAITING_APPROVAL)
                logger.info(
                    "subworkflow.risk.waiting_approval name=%s task_id=%s skill=%s risk=%s",
                    self.workflow_name,
                    task_id,
                    state.get("current_skill"),
                    state.get("risk_level"),
                )
                success = True
                return {**state, "status": TaskStatus.WAITING_APPROVAL.value}

            logger.info(
                "subworkflow.risk.pass name=%s task_id=%s skill=%s",
                self.workflow_name,
                task_id,
                state.get("current_skill"),
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
        if state.get("status") == TaskStatus.WAITING_APPROVAL.value:
            return "WAITING_APPROVAL"
        return "CONTINUE"

    async def _wait_approval(self, state: DomainWorkflowState) -> DomainWorkflowState:
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
        task_id = state["task_id"]
        node_name = "draft_answer"
        started_at = time.perf_counter()
        metrics.on_task_step(task_id=task_id, workflow=self.workflow_name, node=node_name)
        success = False
        retrieval_context = format_retrieval_context(state.get("retrieval_hits", []))
        tool_context = format_tool_context(state.get("tool_trace", []))
        final_context = "\n".join(part for part in (retrieval_context, tool_context) if part.strip())
        logger.info(
            "subworkflow.draft name=%s task_id=%s skill=%s retrieval_hits=%s tools=%s context_len=%s",
            self.workflow_name,
            task_id,
            state.get("current_skill"),
            len(state.get("retrieval_hits", [])),
            len(state.get("tool_trace", [])),
            len(final_context),
        )

        try:
            answer = await self.answer_generator(
                state["message"],
                final_context,
                state.get("skill_instruction", ""),
                state.get("response_contract", ""),
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
