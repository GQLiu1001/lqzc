from __future__ import annotations

from app.memory.mysql_store import MySQLStore


class ApprovalTool:
    def __init__(self, mysql_store: MySQLStore) -> None:
        self.mysql_store = mysql_store

    def request(self, *, task_id: str, approval_action: str) -> None:
        self.mysql_store.create_or_update_approval(
            task_id=task_id,
            approval_action=approval_action,
            status="PENDING",
            approver_id=None,
            comment=None,
        )

    def decide(self, *, task_id: str, approval_action: str, approver_id: str, comment: str | None) -> None:
        status = "APPROVED" if approval_action in {"approve", "edit_and_approve"} else "REJECTED"
        self.mysql_store.create_or_update_approval(
            task_id=task_id,
            approval_action=approval_action,
            status=status,
            approver_id=approver_id,
            comment=comment,
        )

    def get(self, task_id: str) -> dict | None:
        return self.mysql_store.get_approval(task_id=task_id)
