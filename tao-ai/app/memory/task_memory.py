"""提供与任务记忆相关的实现。"""

from __future__ import annotations

from app.memory.mysql_store import MySQLStore
from app.schemas.task import TaskRecord, TaskStatus


class TaskMemory:
    """任务状态管理的业务封装。

    和 SessionMemory 一样，它本质上是 MySQLStore 之上的一层“语义包装”：
    让上层代码从“操作数据库记录”变成“操作任务对象”。
    """
    def __init__(self, mysql_store: MySQLStore) -> None:
        """初始化任务记忆，把运行时依赖和基础状态准备好。"""
        self.mysql_store = mysql_store

    def create(self, *, session_id: str, tenant_id: str | None, user_id: str | None, user_message: str) -> str:
        """创建一条新任务记录，并返回 task_id。"""
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
        risk_level: str | None = None,
        final_response: str | None = None,
    ) -> None:
        """更新任务的执行状态、风险等级或最终回复。"""
        self.mysql_store.update_task(
            task_id=task_id,
            status=status,
            current_agent=current_agent,
            risk_level=risk_level,
            final_response=final_response,
        )

    def get(self, task_id: str) -> TaskRecord | None:
        """按 task_id 读取任务详情。"""
        return self.mysql_store.get_task(task_id=task_id)
