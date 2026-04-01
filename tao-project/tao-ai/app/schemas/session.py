from __future__ import annotations

from pydantic import BaseModel


class SessionMessage(BaseModel):
    role: str
    content: str
    created_at: str | None = None


class SessionDetail(BaseModel):
    session_id: str
    tenant_id: str | None = None
    user_id: str | None = None
    messages: list[SessionMessage]

