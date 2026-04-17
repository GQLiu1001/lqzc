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
    scene: str
    query: str
    top_k: int = 8
    user_context: dict
    extra_filters: dict | None = None


class RAGSearchResult(BaseModel):
    success: bool
    query: str
    rewritten_query: str | None = None
    hits: list[RetrievedChunk] = Field(default_factory=list)
    used_filters: dict = Field(default_factory=dict)
    no_hit: bool = False
