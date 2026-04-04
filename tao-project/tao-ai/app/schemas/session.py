"""提供与会话相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class SessionMessage(BaseModel):
    """定义会话message，用于承载当前模块中的核心逻辑。"""
    role: str
    content: str
    created_at: str | None = None


class SessionDetail(BaseModel):
    """定义会话detail，用于承载当前模块中的核心逻辑。"""
    session_id: str
    tenant_id: str | None = None
    user_id: str | None = None
    messages: list[SessionMessage]

