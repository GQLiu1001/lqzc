"""提供与API相关的实现。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.agent_output import AgentOutput
from app.schemas.eval import EvalCaseResult, EvalRunSummary
from app.schemas.task import TaskRecord


class ChatRequest(BaseModel):
    """聊天接口入参。

    这是前端调用 `/chat` 或 `/tasks/execute` 时最常见的请求体结构。
    """
    session_id: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None
    message: str
    context: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """聊天接口出参。

    它既包含用户最关心的 `answer/reply`，
    也包含调试和前端展示常用的 `agent/skill/evidence/tool_events/status`。
    """
    task_id: str
    session_id: str
    agent: str
    skill: str
    answer: str
    reply: str
    evidence: list[dict] = Field(default_factory=list)
    requires_approval: bool = False
    status: str
    steps_used: int = 1
    tool_events: list[dict] = Field(default_factory=list)

    @classmethod
    def from_agent_output(cls, *, task_id: str, session_id: str, output: AgentOutput) -> "ChatResponse":
        """把工作流输出对象转换成 API 层响应。

        这样工作流层和接口层就不会直接耦合在一起。
        """
        return cls(
            task_id=task_id,
            session_id=session_id,
            agent=output.agent,
            skill=output.skill,
            answer=output.answer,
            reply=output.answer,
            evidence=[item.model_dump() for item in output.evidence],
            requires_approval=output.requires_approval,
            status=output.status,
            steps_used=1,
            tool_events=[item.model_dump() for item in output.tool_trace],
        )


class TaskExecuteRequest(ChatRequest):
    """任务执行接口入参。

    当前它直接复用了 ChatRequest 的全部字段。
    """
    pass


class TaskApproveRequest(BaseModel):
    """审批接口入参。"""
    task_id: str
    approval_action: Literal["approve", "reject", "edit_and_approve"]
    approver_id: str
    comment: str | None = None


class EvalRunRequest(BaseModel):
    """启动评测时的请求体。"""
    dataset_name: str = "smoke"
    max_cases: int | None = None
    stop_on_error: bool = False
    persist: bool = True


class EvalRunResponse(BaseModel):
    """评测结果响应体。

    默认会返回汇总指标；如果 `include_cases=True`，还会附带 case 详情。
    """
    run_id: str
    dataset_name: str
    status: str
    total_cases: int
    passed_cases: int
    route_accuracy: float
    tool_success_rate: float
    retrieval_hit_rate: float
    approval_trigger_precision: float
    pass_rate: float
    avg_latency_ms: float
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    cases: list[EvalCaseResult] = Field(default_factory=list)

    @classmethod
    def from_summary(
        cls,
        summary: EvalRunSummary,
        *,
        include_cases: bool = False,
        cases: list[EvalCaseResult] | None = None,
    ) -> "EvalRunResponse":
        """把评测汇总对象转换成 API 响应。"""
        return cls(
            run_id=summary.run_id,
            dataset_name=summary.dataset_name,
            status=summary.status,
            total_cases=summary.total_cases,
            passed_cases=summary.passed_cases,
            route_accuracy=summary.route_accuracy,
            tool_success_rate=summary.tool_success_rate,
            retrieval_hit_rate=summary.retrieval_hit_rate,
            approval_trigger_precision=summary.approval_trigger_precision,
            pass_rate=summary.pass_rate,
            avg_latency_ms=summary.avg_latency_ms,
            started_at=summary.started_at,
            finished_at=summary.finished_at,
            error=summary.error,
            cases=list(cases or []) if include_cases else [],
        )


class TaskStatusResponse(BaseModel):
    """任务状态查询接口出参。"""
    task: TaskRecord
