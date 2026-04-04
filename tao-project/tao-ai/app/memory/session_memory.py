"""提供与会话记忆相关的实现。"""

from __future__ import annotations

from app.memory.mysql_store import MySQLStore


class SessionMemory:
    """会话消息历史的轻量封装。

    这个类的作用很像“带业务语义的别名层”：
    它底层还是调用 MySQLStore，但方法名变成了更好理解的 `append/history`。
    """
    def __init__(self, mysql_store: MySQLStore) -> None:
        """初始化会话记忆，把运行时依赖和基础状态准备好。"""
        self.mysql_store = mysql_store

    def append(self, *, session_id: str, role: str, content: str) -> None:
        """向指定会话追加一条消息。

        `role` 一般是 `user` 或 `assistant`，表示这条消息是谁说的。
        """
        self.mysql_store.append_message(session_id=session_id, role=role, content=content)

    def history(self, *, session_id: str, limit: int = 20) -> list[dict]:
        """读取会话历史。

        这个方法通常用于多轮对话场景，帮助系统回看最近若干轮消息。
        """
        return self.mysql_store.list_messages(session_id=session_id, limit=limit)
