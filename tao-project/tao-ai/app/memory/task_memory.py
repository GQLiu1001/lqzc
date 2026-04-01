from __future__ import annotations

from app.memory.mysql_store import MySQLStore
from app.schemas.task import TaskRecord, TaskStatus


class TaskMemory:
    def __init__(self, mysql_store: MySQLStore) -> None:
        self.mysql_store = mysql_store

    def create(self, *, session_id: str, tenant_id: str | None, user_id: str | None, user_message: str) -> str:
        return self.mysql_store.create_task(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            user_message=user_message,
        )

    def update(
        self,
        *,
        task_id: str,
        status: TaskStatus | None = None,
        current_agent: str | None = None,
        current_skill: str | None = None,
        risk_level: str | None = None,
        final_response: str | None = None,
    ) -> None:
        self.mysql_store.update_task(
            task_id=task_id,
            status=status,
            current_agent=current_agent,
            current_skill=current_skill,
            risk_level=risk_level,
            final_response=final_response,
        )

    def get(self, task_id: str) -> TaskRecord | None:
        return self.mysql_store.get_task(task_id=task_id)

