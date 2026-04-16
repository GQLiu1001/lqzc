"""任务状态契约 (M1 占位, M2 落库)。"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TaskStatus = Literal[
    "pending",
    "running",
    "waiting_approval",
    "succeeded",
    "failed",
    "expired",
]


class TaskRecord(BaseModel):
    task_id: str
    session_id: str
    skill: Optional[str] = None
    status: TaskStatus = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
