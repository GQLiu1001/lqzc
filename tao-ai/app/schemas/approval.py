"""提供与审批相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class ApprovalRecord(BaseModel):
    """审批记录的数据结构。"""
    task_id: str
    approval_action: str
    approver_id: str | None = None
    comment: str | None = None
    status: str
