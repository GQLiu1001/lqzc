"""HTTP 层请求 / 响应契约。"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="同一会话的唯一标识 (LangGraph thread_id)")
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    # M1 占位,后续走审批 / 多轮
    metadata: dict[str, Any] = Field(default_factory=dict)


class SSEEvent(BaseModel):
    """SSE 事件统一结构;前端按 `event` 字段分发。"""

    event: Literal[
        "node_start",
        "node_end",
        "token",
        "tool_call",
        "tool_result",
        "approval_required",
        "final",
        "error",
    ]
    data: dict[str, Any] = Field(default_factory=dict)
