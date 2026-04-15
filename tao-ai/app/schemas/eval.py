"""提供与评测相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvalCaseExpected(BaseModel):
    """单条评测用例的预期结果定义。

    这里描述“这条 case 理想情况下应该发生什么”：
    应该路由到哪个 agent、要不要审批、至少要有多少证据等。
    """
    agent: str | None = None
    requires_approval: bool | None = None
    min_evidence_hits: int | None = None
    must_include_keywords: list[str] = Field(default_factory=list)
    any_of_keywords: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    """单条评测用例。"""
    case_id: str
    message: str
    session_id: str | None = None
    tenant_id: str | None = "eval"
    user_id: str | None = "eval"
    context: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    expected: EvalCaseExpected = Field(default_factory=EvalCaseExpected)


class EvalCaseResult(BaseModel):
    """单条评测用例的实际执行结果。"""
    case_id: str
    message: str
    expected_agent: str | None = None
    expected_requires_approval: bool | None = None
    actual_agent: str | None = None
    actual_requires_approval: bool = False
    status: str = "FAILED"
    retrieval_hits: int = 0
    tool_calls_total: int = 0
    tool_calls_success: int = 0
    latency_ms: float = 0.0
    passed_route: bool = False
    passed_retrieval: bool = False
    passed_approval: bool = False
    passed_keywords: bool = False
    passed: bool = False
    error: str | None = None


class EvalRunSummary(BaseModel):
    """一次评测运行的汇总结果。"""
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


class EvalRunDetail(BaseModel):
    """一次评测运行的完整详情，包含摘要和各 case 结果。"""
    summary: EvalRunSummary
    cases: list[EvalCaseResult] = Field(default_factory=list)
