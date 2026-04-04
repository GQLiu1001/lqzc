"""提供与检索相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class Evidence(BaseModel):
    """定义evidence，用于承载当前模块中的核心逻辑。"""
    source: str
    content: str
    score: float | None = None
    metadata: dict | None = None


class RetrievalTrace(BaseModel):
    """定义检索trace，用于承载当前模块中的核心逻辑。"""
    query: str
    domain: str
    collection: str
    hits: int

