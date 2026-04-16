"""Tool 调用与结果契约。"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ToolStatus = Literal["ok", "error", "pending_approval", "rejected", "timeout"]


class ToolCallRecord(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    status: ToolStatus = "ok"
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


class RetrievalHit(BaseModel):
    doc_id: str
    score: float
    text: str
    source: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
