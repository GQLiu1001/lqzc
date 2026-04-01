from __future__ import annotations

from pydantic import BaseModel


class ApprovalRecord(BaseModel):
    task_id: str
    approval_action: str
    approver_id: str | None = None
    comment: str | None = None
    status: str

