"""提供与会话相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class SessionMessage(BaseModel):
    """会话中的一条消息。"""
    role: str
    content: str
    created_at: str | None = None


class SessionDetail(BaseModel):
    """一个会话及其历史消息。"""
    session_id: str
    tenant_id: str | None = None
    user_id: str | None = None
    messages: list[SessionMessage]
