"""会话 / 消息契约。"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None  # tool 消息的工具名
    created_at: datetime = Field(default_factory=datetime.utcnow)
