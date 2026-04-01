from __future__ import annotations

from app.memory.mysql_store import MySQLStore


class SessionMemory:
    def __init__(self, mysql_store: MySQLStore) -> None:
        self.mysql_store = mysql_store

    def append(self, *, session_id: str, role: str, content: str) -> None:
        self.mysql_store.append_message(session_id=session_id, role=role, content=content)

    def history(self, *, session_id: str, limit: int = 20) -> list[dict]:
        return self.mysql_store.list_messages(session_id=session_id, limit=limit)

