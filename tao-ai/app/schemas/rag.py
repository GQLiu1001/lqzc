from datetime import datetime

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    content: str
    score: float
    rerank_score: float | None = None
    domain: str
    scene: str | None = None
    source_type: str
    version: str | None = None
    effective_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class RAGSearchRequest(BaseModel):
    domain: str
    scene: str = "general"
    query: str
    top_k: int = 8
    user_context: dict
    extra_filters: dict | None = None
    session_id: str | None = None


class RAGSearchResult(BaseModel):
    success: bool
    query: str
    rewritten_query: str | None = None
    hits: list[RetrievedChunk] = Field(default_factory=list)
    used_filters: dict = Field(default_factory=dict)
    no_hit: bool = False
    context_text: str = ""
    retrieved_docs_count: int = 0
    search_mode: str = "local-lexical"
    message: str | None = None
    error_code: str | None = None
    latency_ms: int | None = None
