from __future__ import annotations

from pydantic import BaseModel


class Evidence(BaseModel):
    source: str
    content: str
    score: float | None = None
    metadata: dict | None = None


class RetrievalTrace(BaseModel):
    query: str
    domain: str
    collection: str
    hits: int

