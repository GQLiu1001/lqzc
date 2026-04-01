from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.agent_output import AgentOutput
from app.schemas.eval import EvalCaseResult, EvalRunSummary
from app.schemas.task import TaskRecord


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None
    message: str
    context: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
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
    pass


class TaskApproveRequest(BaseModel):
    task_id: str
    approval_action: Literal["approve", "reject", "edit_and_approve"]
    approver_id: str
    comment: str | None = None


class EvalRunRequest(BaseModel):
    dataset_name: str = "smoke"
    max_cases: int | None = None
    stop_on_error: bool = False
    persist: bool = True


class EvalRunResponse(BaseModel):
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
    task: TaskRecord
