"""提供与总控工作流相关的实现。"""

from __future__ import annotations

import logging
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.customer_service.agent import CustomerServiceAgent
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.warehouse.agent import WarehouseAgent
from app.memory.memory_store import MemoryStore
from app.observability.metrics import metrics
from app.schemas.agent_output import AgentOutput
from app.schemas.api import ChatRequest, TaskApproveRequest
from app.schemas.retrieval import Evidence
from app.schemas.task import TaskRecord, TaskStatus
from app.schemas.tool import ToolTrace
from app.tools.approval_tools.approval_tool import ApprovalTool
from app.tools.approval_tools.action_executor import ActionExecutor
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools
from app.tools.rag_tools.retriever_tool import RetrieverTool
from app.workflows.customer_service_workflow import CustomerServiceWorkflow
from app.workflows.domain_subworkflow import DomainWorkflowState
from app.workflows.warehouse_workflow import WarehouseWorkflow


logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    """总控工作流在节点之间传递的状态对象。

    可以把它理解成“任务上下文的大包裹”：
    每经过一个节点，节点都会从这里读取自己需要的信息，
    再把新产出的结果回写进去，供后面的节点继续使用。
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


class SupervisorWorkflow:
    """封装总控工作流，负责把多个步骤按状态图串联起来执行。"""
    def __init__(
        self,
        *,
        memory: MemoryStore,
        supervisor_agent: SupervisorAgent,
        customer_agent: CustomerServiceAgent,
        warehouse_agent: WarehouseAgent,
        retriever_tool: RetrieverTool,
        business_tools: LQZCBusinessTools,
        approval_tool: ApprovalTool,
    ) -> None:
        """初始化总控工作流，把运行时依赖和基础状态准备好。"""
        self.memory = memory
        self.supervisor_agent = supervisor_agent
        self.approval_tool = approval_tool
        self.action_executor = ActionExecutor(mysql_store=memory.mysql, business_tools=business_tools)
        self.customer_workflow = CustomerServiceWorkflow(
            memory=memory,
            customer_agent=customer_agent,
            retriever_tool=retriever_tool,
            business_tools=business_tools,
            approval_tool=approval_tool,
        )
        self.warehouse_workflow = WarehouseWorkflow(
            memory=memory,
            warehouse_agent=warehouse_agent,
            retriever_tool=retriever_tool,
            business_tools=business_tools,
            approval_tool=approval_tool,
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建总控状态图。

        这里是整个系统最外层的“总流程编排器”：
        1. 先解析输入，创建 session/task。
        2. 再让 supervisor 判断当前问题属于哪个业务域。
        3. 然后把任务转交给具体子工作流执行。
        4. 最后统一收口，写回会话和任务最终状态。

        LangGraph 的 `StateGraph` 可以理解成一个带状态传递能力的流程图。
        """
        graph = StateGraph(WorkflowState)
        graph.add_node("parse_input", self._parse_input)
        graph.add_node("route_request", self._route_request)
        graph.add_node("dispatch_customer_subagent", self._dispatch_customer_subagent)
        graph.add_node("dispatch_warehouse_subagent", self._dispatch_warehouse_subagent)
        graph.add_node("finalize", self._finalize)

        graph.add_edge(START, "parse_input")
        graph.add_edge("parse_input", "route_request")
        graph.add_conditional_edges(
            "route_request",
            self._agent_branch,
            {
                "CUSTOMER": "dispatch_customer_subagent",
                "WAREHOUSE": "dispatch_warehouse_subagent",
            },
        )
        graph.add_edge("dispatch_customer_subagent", "finalize")
        graph.add_edge("dispatch_warehouse_subagent", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    async def _parse_input(self, state: WorkflowState) -> WorkflowState:
        """解析最初输入，并创建运行时任务。

        这个节点做的是“开单”动作：
        - 确保 session 存在，方便多轮对话复用上下文。
        - 创建 task，方便后续追踪一次请求从开始到结束的状态。
        - 把用户原始消息写入会话历史。

        注意：这里还没开始回答问题，只是在做任务登记和初始化。
        """
        node_name = "parse_input"
        node_started = time.perf_counter()
        success = False
        task_id = ""
        try:
            # 如果前端没传 session_id，这里会自动创建一个新的会话。
            session_id = self.memory.mysql.ensure_session(
                state.get("session_id"),
                tenant_id=state.get("tenant_id"),
                user_id=state.get("user_id"),
            )
            # 一个 session 下可以有多条 task。task 表示“这一次具体请求”的执行记录。
            task_id = self.memory.task.create(
                session_id=session_id,
                tenant_id=state.get("tenant_id"),
                user_id=state.get("user_id"),
                user_message=state["message"],
            )
            metrics.on_task_created(task_id=task_id)
            metrics.on_task_step(task_id=task_id, workflow="supervisor", node=node_name)
            metrics.record_task_transition(
                from_status="INIT",
                to_status=TaskStatus.NEW.value,
                agent="supervisor",
            )
            # 把用户原话写入会话历史，后面排障或做多轮上下文时会用到。
            self.memory.session.append(session_id=session_id, role="user", content=state["message"])
            logger.info(
                "workflow.parse_input task_id=%s session_id=%s tenant_id=%s user_id=%s message_len=%s",
                task_id,
                session_id,
                state.get("tenant_id"),
                state.get("user_id"),
                len(state["message"]),
            )

            success = True
            return {
                **state,
                "session_id": session_id,
                "task_id": task_id,
                "status": TaskStatus.NEW.value,
                "tool_trace": [],
                "retrieval_hits": [],
                "evidence": [],
            }
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - node_started,
                success=success,
            )

    async def _route_request(self, state: WorkflowState) -> WorkflowState:
        """把用户请求路由到合适的业务域。

        这是整个系统里的“分诊台”：
        - 先判断该问题更像客服问题还是仓储问题。
        - 同时给出风险等级、是否需要审批等元信息。

        这个节点本身不回答问题，只负责做“派单”。
        """
        node_name = "route_request"
        node_started = time.perf_counter()
        success = False
        task_id = state["task_id"]
        metrics.on_task_step(task_id=task_id, workflow="supervisor", node=node_name)
        try:
            # SupervisorAgent 会先走规则路由；分数不够时，再考虑让 LLM 兜底判断。
            decision = await self.supervisor_agent.route(state["message"], context=state.get("context", {}))
            logger.info(
                "workflow.route task_id=%s agent=%s risk=%s approval=%s source=%s confidence=%s reason=%s",
                task_id,
                decision.agent,
                decision.risk_level,
                decision.requires_approval,
                decision.route_source,
                decision.route_confidence,
                decision.route_reason,
            )
            metrics.record_task_transition(
                from_status=str(state.get("status") or TaskStatus.NEW.value),
                to_status=TaskStatus.ROUTED.value,
                agent=decision.agent,
            )
            metrics.on_task_routed(
                task_id=task_id,
                agent=decision.agent,
                route_source=decision.route_source,
            )
            self.memory.task.update(
                task_id=task_id,
                status=TaskStatus.ROUTED,
                current_agent=decision.agent,
                risk_level=decision.risk_level,
            )
            # 虽然这里不是传统“工具调用”，但仍然把路由结果落库，便于后面回放。
            self.memory.mysql.insert_tool_trace(
                task_id=task_id,
                tool_name="domain_router",
                arguments={
                    "message": state["message"],
                    "context": state.get("context", {}),
                },
                result_preview=(
                    f"source={decision.route_source} confidence={decision.route_confidence} "
                    f"agent={decision.agent} reason={decision.route_reason}"
                ),
                result={
                    "route_source": decision.route_source,
                    "route_confidence": decision.route_confidence,
                    "agent": decision.agent,
                    "risk_level": decision.risk_level,
                    "requires_approval": decision.requires_approval,
                    "route_reason": decision.route_reason,
                },
                status="SUCCESS",
            )
            success = True
            return {
                **state,
                "status": TaskStatus.ROUTED.value,
                "current_agent": decision.agent,
                "route_reason": decision.route_reason,
                "route_source": decision.route_source,
                "route_confidence": decision.route_confidence,
                "risk_level": decision.risk_level,
                "requires_approval": decision.requires_approval,
                "retrieval_domain": decision.retrieval_domain,
            }
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - node_started,
                success=success,
            )

    def _agent_branch(self, state: WorkflowState) -> str:
        """根据路由结果决定进入哪个子工作流。"""
        if state.get("current_agent") == "warehouse":
            return "WAREHOUSE"
        return "CUSTOMER"

    async def _dispatch_customer_subagent(self, state: WorkflowState) -> WorkflowState:
        """作为内部辅助步骤，完成dispatch客服subagent相关处理。"""
        node_name = "dispatch_customer_subagent"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=state["task_id"], workflow="supervisor", node=node_name)
        try:
            logger.info(
                "workflow.dispatch task_id=%s target=customer_subgraph",
                state["task_id"],
            )
            result = await self._dispatch_to_subworkflow(state, self.customer_workflow)
            success = True
            return result
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def _dispatch_warehouse_subagent(self, state: WorkflowState) -> WorkflowState:
        """作为内部辅助步骤，完成dispatch仓储subagent相关处理。"""
        node_name = "dispatch_warehouse_subagent"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=state["task_id"], workflow="supervisor", node=node_name)
        try:
            logger.info(
                "workflow.dispatch task_id=%s target=warehouse_subgraph",
                state["task_id"],
            )
            result = await self._dispatch_to_subworkflow(state, self.warehouse_workflow)
            success = True
            return result
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def _dispatch_to_subworkflow(
        self,
        state: WorkflowState,
        subworkflow: CustomerServiceWorkflow | WarehouseWorkflow,
    ) -> WorkflowState:
        """把总控状态转换成子工作流能理解的状态，再真正执行子流程。

        总控层只负责“分流”和“收口”，真正的检索、工具调用、审批等待、回答生成，
        都在具体的 domain subworkflow 里完成。
        """
        dispatch_started = time.perf_counter()
        dispatch_status = "SUCCESS"
        # 这里是在做“状态适配”：
        # 总控工作流和子工作流字段大体相同，但仍显式拷贝一次，
        # 这样每层的职责更清晰，也方便后面扩字段。
        sub_state: DomainWorkflowState = {
            "session_id": state["session_id"],
            "user_id": state.get("user_id"),
            "tenant_id": state.get("tenant_id"),
            "context": state.get("context", {}),
            "message": state["message"],
            "task_id": state["task_id"],
            "status": state.get("status", TaskStatus.ROUTED.value),
            "current_agent": state.get("current_agent", "customer_service"),
            "route_reason": state.get("route_reason", ""),
            "route_source": state.get("route_source", "rule"),
            "route_confidence": state.get("route_confidence"),
            "risk_level": state.get("risk_level", "LOW"),
            "requires_approval": bool(state.get("requires_approval", False)),
            "retrieval_domain": state.get("retrieval_domain", state.get("current_agent", "customer_service")),
            "collection_name": state.get("collection_name", ""),
            "retrieval_hits": list(state.get("retrieval_hits", [])),
            "tool_trace": list(state.get("tool_trace", [])),
            "evidence": list(state.get("evidence", [])),
            "answer": state.get("answer", ""),
        }

        try:
            result = await subworkflow.run(sub_state)
        except Exception as exc:
            dispatch_status = "FAILED"
            logger.exception(
                "workflow.dispatch.failed task_id=%s subgraph=%s error=%s",
                state["task_id"],
                subworkflow.workflow_name,
                exc,
            )
            self.memory.task.update(task_id=state["task_id"], status=TaskStatus.FAILED)
            self.memory.mysql.insert_tool_trace(
                task_id=state["task_id"],
                tool_name=f"{subworkflow.workflow_name}_dispatch",
                arguments={"agent": state.get("current_agent"), "message": state["message"]},
                result_preview=str(exc),
                result={"error": str(exc)},
                status="FAILED",
            )
            return {
                **state,
                "status": TaskStatus.FAILED.value,
                "answer": "系统处理过程中发生异常，请稍后重试或联系管理员。",
            }
        finally:
            metrics.observe_subworkflow_dispatch(
                target=subworkflow.workflow_name,
                status=dispatch_status,
                duration_seconds=time.perf_counter() - dispatch_started,
            )

        # 子工作流执行完后，只把关键结果合并回总控状态。
        return {
            **state,
            "status": result.get("status", state.get("status", TaskStatus.COMPLETED.value)),
            "collection_name": result.get("collection_name", state.get("collection_name", "")),
            "retrieval_hits": result.get("retrieval_hits", state.get("retrieval_hits", [])),
            "tool_trace": result.get("tool_trace", state.get("tool_trace", [])),
            "evidence": result.get("evidence", state.get("evidence", [])),
            "answer": result.get("answer", state.get("answer", "")),
        }

    async def _finalize(self, state: WorkflowState) -> WorkflowState:
        """收尾并落库最终结果。

        这里做三件事：
        - 统一决定任务最终状态。
        - 把 assistant 的回复写入会话历史。
        - 更新 task 表，形成一条完整的执行闭环。

        为什么要专门有 finalize 节点：
        因为无论前面走客服还是仓储，最后都需要一套统一的收尾逻辑。
        """
        task_id = state["task_id"]
        node_name = "finalize"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=task_id, workflow="supervisor", node=node_name)
        try:
            # 子流程可能返回很多中间状态，这里统一收敛成最终可对外展示的状态。
            raw_status = state.get("status", TaskStatus.COMPLETED.value)
            terminal_keep = {
                TaskStatus.WAITING_APPROVAL.value,
                TaskStatus.FAILED.value,
                TaskStatus.ESCALATED.value,
                TaskStatus.REJECTED.value,
                TaskStatus.APPROVED.value,
            }
            status = raw_status if raw_status in terminal_keep else TaskStatus.COMPLETED.value
            answer = state.get("answer", "") or (
                "系统暂时没有返回结果，请稍后重试。"
                if status == TaskStatus.FAILED.value
                else ""
            )

            # 把最终回复写入聊天历史，这样下轮对话就能看到上一轮 assistant 说了什么。
            self.memory.session.append(session_id=state["session_id"], role="assistant", content=answer)

            status_enum = TaskStatus(status) if status in TaskStatus._value2member_map_ else TaskStatus.COMPLETED
            if str(raw_status) != status_enum.value:
                metrics.record_task_transition(
                    from_status=str(raw_status),
                    to_status=status_enum.value,
                    agent=str(state.get("current_agent") or "unknown"),
                )
            self.memory.task.update(
                task_id=task_id,
                status=status_enum,
                final_response=answer,
            )
            logger.info(
                "workflow.finalize task_id=%s session_id=%s status=%s answer_len=%s",
                task_id,
                state["session_id"],
                status_enum.value,
                len(answer),
            )
            metrics.on_task_finished(task_id=task_id, status=status_enum.value)
            success = True
            return {**state, "status": status_enum.value, "answer": answer}
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - started_at,
                success=success,
            )

    async def run_chat(self, payload: ChatRequest) -> tuple[str, str, AgentOutput]:
        """聊天接口真正调用的总入口。

        API 层收到 `/chat` 请求后，最终就是进入这里。
        你可以把它理解成“把 HTTP 请求翻译成工作流输入，然后等工作流跑完”。
        """
        initial_state: WorkflowState = {
            "session_id": payload.session_id or "",
            "user_id": payload.user_id,
            "tenant_id": payload.tenant_id,
            "context": payload.context,
            "message": payload.message,
        }
        try:
            state = await self.graph.ainvoke(initial_state)
        except Exception:
            logger.exception(
                "workflow.run_chat.failed session_id=%s tenant_id=%s user_id=%s",
                payload.session_id,
                payload.tenant_id,
                payload.user_id,
            )
            raise

        # LangGraph 里保存的是普通 dict，这里再转换成接口层约定的结构化对象。
        output = AgentOutput(
            agent=state.get("current_agent", "supervisor"),
            answer=state.get("answer", ""),
            requires_approval=state.get("status") == TaskStatus.WAITING_APPROVAL.value,
            status=state.get("status", TaskStatus.COMPLETED.value),
            risk_level=state.get("risk_level", "LOW"),
            evidence=[Evidence(**item) for item in state.get("evidence", [])],
            tool_trace=[ToolTrace(**item) for item in state.get("tool_trace", [])],
        )
        return state["task_id"], state["session_id"], output

    def approve_task(self, payload: TaskApproveRequest) -> TaskRecord | None:
        """处理人工审批。

        当某个请求被标记为高风险时，子工作流不会直接执行危险动作，
        而是先把任务挂起到 WAITING_APPROVAL。
        这个方法就是审批人点击“通过/拒绝”后进入的入口。
        """
        task = self.memory.task.get(payload.task_id)
        if task is None:
            logger.warning("workflow.approve.not_found task_id=%s", payload.task_id)
            return None

        normalized_action = payload.approval_action.strip().lower()
        if normalized_action not in {"approve", "reject", "edit_and_approve"}:
            raise ValueError(f"Unsupported approval_action: {payload.approval_action}")
        if task.status != TaskStatus.WAITING_APPROVAL:
            raise ValueError(
                f"Task status conflict: task_id={payload.task_id} current_status={task.status.value} "
                f"expected_status={TaskStatus.WAITING_APPROVAL.value}"
            )

        logger.info(
            "workflow.approve task_id=%s action=%s approver=%s",
            payload.task_id,
            normalized_action,
            payload.approver_id,
        )
        self.approval_tool.decide(
            task_id=payload.task_id,
            approval_action=normalized_action,
            approver_id=payload.approver_id,
            comment=payload.comment,
        )
        if normalized_action == "reject":
            metrics.record_task_transition(
                from_status=task.status.value,
                to_status=TaskStatus.REJECTED.value,
                agent=str(task.current_agent or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.REJECTED,
                final_response=f"审批拒绝：{payload.comment or '未提供原因'}",
            )
            return self.memory.task.get(payload.task_id)

        metrics.record_task_transition(
            from_status=task.status.value,
            to_status=TaskStatus.APPROVED.value,
            agent=str(task.current_agent or "unknown"),
        )
        self.memory.task.update(task_id=payload.task_id, status=TaskStatus.APPROVED)
        metrics.record_task_transition(
            from_status=TaskStatus.APPROVED.value,
            to_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
            agent=str(task.current_agent or "unknown"),
        )
        self.memory.task.update(task_id=payload.task_id, status=TaskStatus.EXECUTING_APPROVED_ACTION)

        execution_result = self.action_executor.execute_task_actions(
            task_id=payload.task_id,
            approval_action=normalized_action,
            approver_id=payload.approver_id,
            comment=payload.comment,
        )
        execution_status = str(execution_result.get("status") or "FAILED").upper()

        if execution_status == "SUCCESS":
            summary = execution_result.get("summary") if isinstance(execution_result.get("summary"), dict) else {}
            final_text = (
                f"审批通过，动作已执行成功。"
                f" success={summary.get('success_count', 0)}"
                f", skipped={summary.get('skipped_count', 0)}"
            )
            metrics.record_task_transition(
                from_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
                to_status=TaskStatus.COMPLETED.value,
                agent=str(task.current_agent or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.COMPLETED,
                final_response=final_text,
            )
        elif execution_status == "NO_ACTION":
            final_text = "审批通过，但未发现可执行动作。"
            metrics.record_task_transition(
                from_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
                to_status=TaskStatus.APPROVED.value,
                agent=str(task.current_agent or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.APPROVED,
                final_response=final_text,
            )
        elif execution_status == "SKIPPED":
            final_text = "审批通过，动作已执行过，本次未重复执行。"
            metrics.record_task_transition(
                from_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
                to_status=TaskStatus.COMPLETED.value,
                agent=str(task.current_agent or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.COMPLETED,
                final_response=final_text,
            )
        else:
            final_text = f"审批通过，但动作执行失败：{execution_result.get('message', 'unknown error')}"
            metrics.record_task_transition(
                from_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
                to_status=TaskStatus.FAILED.value,
                agent=str(task.current_agent or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.FAILED,
                final_response=final_text,
            )
        return self.memory.task.get(payload.task_id)

    def get_task(self, task_id: str) -> TaskRecord | None:
        """处理GET任务相关逻辑，并返回当前步骤需要的结果。"""
        return self.memory.task.get(task_id)

    def get_session_messages(self, session_id: str) -> list[dict]:
        """处理GET会话messages相关逻辑，并返回当前步骤需要的结果。"""
        return self.memory.session.history(session_id=session_id, limit=50)
