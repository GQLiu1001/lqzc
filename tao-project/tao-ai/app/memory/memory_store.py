"""提供与记忆存储相关的实现。"""

from __future__ import annotations

from app.memory.mysql_store import MySQLStore
from app.memory.session_memory import SessionMemory
from app.memory.task_memory import TaskMemory


class MemoryStore:
    """记忆层门面对象。

    它本身不实现复杂逻辑，而是把几类常用存储能力统一挂到一个入口下：
    - `mysql`：底层数据库访问
    - `session`：会话消息历史
    - `task`：任务状态管理

    这样上层工作流只需要依赖一个 `memory`，不需要分别注入很多存储类。
    """
    def __init__(self) -> None:
        """创建底层存储对象，并暴露更贴近业务语义的子能力。"""
        self.mysql = MySQLStore()
        self.session = SessionMemory(self.mysql)
        self.task = TaskMemory(self.mysql)
