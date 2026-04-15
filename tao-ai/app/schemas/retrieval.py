"""提供与检索相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class Evidence(BaseModel):
    """一条检索证据。

    最终回答如果引用了知识库内容，通常会以这种结构返回给前端或评测层。
    """
    source: str
    content: str
    score: float | None = None
    metadata: dict | None = None


class RetrievalTrace(BaseModel):
    """一次检索动作的摘要信息。"""
    query: str
    domain: str
    collection: str
    hits: int
