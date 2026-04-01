from __future__ import annotations

from app.memory.mysql_store import MySQLStore
from app.memory.session_memory import SessionMemory
from app.memory.task_memory import TaskMemory


class MemoryStore:
    def __init__(self) -> None:
        self.mysql = MySQLStore()
        self.session = SessionMemory(self.mysql)
        self.task = TaskMemory(self.mysql)
