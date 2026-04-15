"""提供与任务相关的实现。"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务生命周期中的所有状态枚举。

    这些状态串起来，基本就是一条请求在系统里流转的全过程。
    """
    NEW = "NEW"
    ROUTED = "ROUTED"
    RETRIEVING = "RETRIEVING"
    TOOL_RUNNING = "TOOL_RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING_APPROVED_ACTION = "EXECUTING_APPROVED_ACTION"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class TaskRecord(BaseModel):
    """任务主记录。"""
    task_id: str
    session_id: str
    tenant_id: str | None = None
    user_id: str | None = None
    status: TaskStatus
    current_agent: str | None = None
    risk_level: str = Field(default="LOW")
    final_response: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
