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


class SupervisorWorkflow:
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
        node_name = "parse_input"
        node_started = time.perf_counter()
        success = False
        task_id = ""
        try:
            session_id = self.memory.mysql.ensure_session(
                state.get("session_id"),
                tenant_id=state.get("tenant_id"),
                user_id=state.get("user_id"),
            )
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
                skill="router",
            )
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
        node_name = "route_request"
        node_started = time.perf_counter()
        success = False
        task_id = state["task_id"]
        metrics.on_task_step(task_id=task_id, workflow="supervisor", node=node_name)
        try:
            decision = await self.supervisor_agent.route(state["message"], context=state.get("context", {}))
            logger.info(
                "workflow.route task_id=%s agent=%s skill=%s risk=%s approval=%s source=%s confidence=%s reason=%s",
                task_id,
                decision.agent,
                decision.skill,
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
                skill=decision.skill,
            )
            metrics.on_task_routed(
                task_id=task_id,
                agent=decision.agent,
                skill=decision.skill,
                route_source=decision.route_source,
            )
            self.memory.task.update(
                task_id=task_id,
                status=TaskStatus.ROUTED,
                current_agent=decision.agent,
                current_skill=decision.skill,
                risk_level=decision.risk_level,
            )
            self.memory.mysql.insert_tool_trace(
                task_id=task_id,
                tool_name="skill_router",
                arguments={
                    "message": state["message"],
                    "context": state.get("context", {}),
                },
                result_preview=(
                    f"source={decision.route_source} confidence={decision.route_confidence} "
                    f"agent={decision.agent} skill={decision.skill} reason={decision.route_reason}"
                ),
                result={
                    "route_source": decision.route_source,
                    "route_confidence": decision.route_confidence,
                    "agent": decision.agent,
                    "skill": decision.skill,
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
                "current_skill": decision.skill,
                "route_reason": decision.route_reason,
                "route_source": decision.route_source,
                "route_confidence": decision.route_confidence,
                "risk_level": decision.risk_level,
                "requires_approval": decision.requires_approval,
                "retrieval_domain": decision.retrieval_domain,
                "skill_instruction": decision.system_instruction,
                "response_contract": decision.response_contract,
                "tool_hints": list(decision.tool_hints),
            }
        finally:
            metrics.observe_node_duration(
                workflow="supervisor",
                node=node_name,
                duration_seconds=time.perf_counter() - node_started,
                success=success,
            )

    def _agent_branch(self, state: WorkflowState) -> str:
        if state.get("current_agent") == "warehouse":
            return "WAREHOUSE"
        return "CUSTOMER"

    async def _dispatch_customer_subagent(self, state: WorkflowState) -> WorkflowState:
        node_name = "dispatch_customer_subagent"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=state["task_id"], workflow="supervisor", node=node_name)
        try:
            logger.info(
                "workflow.dispatch task_id=%s target=customer_subgraph skill=%s",
                state["task_id"],
                state.get("current_skill"),
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
        node_name = "dispatch_warehouse_subagent"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=state["task_id"], workflow="supervisor", node=node_name)
        try:
            logger.info(
                "workflow.dispatch task_id=%s target=warehouse_subgraph skill=%s",
                state["task_id"],
                state.get("current_skill"),
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
        dispatch_started = time.perf_counter()
        dispatch_status = "SUCCESS"
        sub_state: DomainWorkflowState = {
            "session_id": state["session_id"],
            "user_id": state.get("user_id"),
            "tenant_id": state.get("tenant_id"),
            "context": state.get("context", {}),
            "message": state["message"],
            "task_id": state["task_id"],
            "status": state.get("status", TaskStatus.ROUTED.value),
            "current_agent": state.get("current_agent", "customer_service"),
            "current_skill": state.get("current_skill", "order_status_explain_skill"),
            "route_reason": state.get("route_reason", ""),
            "route_source": state.get("route_source", "rule"),
            "route_confidence": state.get("route_confidence"),
            "risk_level": state.get("risk_level", "LOW"),
            "requires_approval": bool(state.get("requires_approval", False)),
            "retrieval_domain": state.get("retrieval_domain", state.get("current_agent", "customer_service")),
            "skill_instruction": state.get("skill_instruction", ""),
            "response_contract": state.get("response_contract", ""),
            "tool_hints": list(state.get("tool_hints", [])),
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
                arguments={"skill": state.get("current_skill"), "message": state["message"]},
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
        task_id = state["task_id"]
        node_name = "finalize"
        started_at = time.perf_counter()
        success = False
        metrics.on_task_step(task_id=task_id, workflow="supervisor", node=node_name)
        try:
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

            self.memory.session.append(session_id=state["session_id"], role="assistant", content=answer)

            status_enum = TaskStatus(status) if status in TaskStatus._value2member_map_ else TaskStatus.COMPLETED
            if str(raw_status) != status_enum.value:
                metrics.record_task_transition(
                    from_status=str(raw_status),
                    to_status=status_enum.value,
                    agent=str(state.get("current_agent") or "unknown"),
                    skill=str(state.get("current_skill") or "unknown"),
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

        output = AgentOutput(
            agent=state.get("current_agent", "supervisor"),
            skill=state.get("current_skill", "generic_skill"),
            answer=state.get("answer", ""),
            requires_approval=state.get("status") == TaskStatus.WAITING_APPROVAL.value,
            status=state.get("status", TaskStatus.COMPLETED.value),
            risk_level=state.get("risk_level", "LOW"),
            evidence=[Evidence(**item) for item in state.get("evidence", [])],
            tool_trace=[ToolTrace(**item) for item in state.get("tool_trace", [])],
        )
        return state["task_id"], state["session_id"], output

    def approve_task(self, payload: TaskApproveRequest) -> TaskRecord | None:
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
                skill=str(task.current_skill or "unknown"),
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
            skill=str(task.current_skill or "unknown"),
        )
        self.memory.task.update(task_id=payload.task_id, status=TaskStatus.APPROVED)
        metrics.record_task_transition(
            from_status=TaskStatus.APPROVED.value,
            to_status=TaskStatus.EXECUTING_APPROVED_ACTION.value,
            agent=str(task.current_agent or "unknown"),
            skill=str(task.current_skill or "unknown"),
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
                skill=str(task.current_skill or "unknown"),
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
                skill=str(task.current_skill or "unknown"),
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
                skill=str(task.current_skill or "unknown"),
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
                skill=str(task.current_skill or "unknown"),
            )
            self.memory.task.update(
                task_id=payload.task_id,
                status=TaskStatus.FAILED,
                final_response=final_text,
            )
        return self.memory.task.get(payload.task_id)

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self.memory.task.get(task_id)

    def get_session_messages(self, session_id: str) -> list[dict]:
        return self.memory.session.history(session_id=session_id, limit=50)
