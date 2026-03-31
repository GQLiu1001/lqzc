"""Tiny SQLite store for chat history and tool traces.

The first version keeps persistence intentionally simple:

- transcript messages: only user and final assistant turns
- tool call logs: each tool invocation with arguments and result preview

This mirrors the learning goal from learn-claude-code:
cleanly separate the *agent loop* from the *harness state*.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class StoredMessage:
    role: str
    content: str


class SQLiteStore:
    """Persist chat sessions in a single local SQLite file."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    result_preview TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id) VALUES (?)",
                (session_id,),
            )
        return session_id

    def ensure_session(self, session_id: str | None) -> str:
        if session_id:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT session_id FROM sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
            if row:
                return session_id
        return self.create_session()

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )

    def list_messages(self, session_id: str) -> list[StoredMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
        return [StoredMessage(role=row[0], content=row[1]) for row in rows]

    def append_tool_call(self, session_id: str, tool_name: str, arguments: dict, result_preview: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tool_calls (session_id, tool_name, arguments_json, result_preview)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    tool_name,
                    json.dumps(arguments, ensure_ascii=False),
                    result_preview[:800],
                ),
            )

