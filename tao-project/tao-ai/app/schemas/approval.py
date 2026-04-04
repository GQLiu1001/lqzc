"""提供与审批相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class ApprovalRecord(BaseModel):
    """表示审批record，用于承载一条运行时记录。"""
    task_id: str
    approval_action: str
    approver_id: str | None = None
    comment: str | None = None
    status: str

