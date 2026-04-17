from pydantic import BaseModel, Field


class EvalSample(BaseModel):
    id: str
    domain: str
    scene: str | None = None
    question: str
    user_context: dict = Field(default_factory=dict)
    expected_doc_ids: list[str] = Field(default_factory=list)
    reference_answer: str | None = None
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)


class RetrievalMetrics(BaseModel):
    hit: bool = False
    hit_at_k: int | None = None
    recall: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    no_hit: bool = False
    retrieved_doc_ids: list[str] = Field(default_factory=list)


class JudgeScore(BaseModel):
    rule_pass: bool = True
    rule_detail: dict = Field(default_factory=dict)
    correctness: float = 0.0
    groundedness: float = 0.0
    permission_safe: bool = True
    llm_detail: dict = Field(default_factory=dict)


class EvalSampleResult(BaseModel):
    sample_id: str
    domain: str
    scene: str | None = None
    question: str
    user_context: dict = Field(default_factory=dict)
    reference_answer: str | None = None
    actual_answer: str
    retrieved: RetrievalMetrics
    judge: JudgeScore
    latency_ms: int
    passed: bool = True
    failure_reason: str | None = None


class EvalRunResult(BaseModel):
    run_id: str
    dataset_name: str
    total_samples: int
    hit_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float
    groundedness: float
    correctness: float
    permission_safety: float
    no_hit_rate: float
    duration_ms: int
    samples: list[EvalSampleResult] = Field(default_factory=list)
