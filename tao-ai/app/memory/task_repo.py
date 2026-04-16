"""Task / ToolCall / Approval CRUD 仓储。

use_stub_stores=True → InMemoryTaskRepo (dict)
use_stub_stores=False → MySqlTaskRepo (aiomysql)
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional

from app.config import get_settings
from app.schemas.approval import ApprovalRecord
from app.schemas.task import TaskRecord, TaskStatus
from app.schemas.tool import ToolCallRecord

logger = logging.getLogger(__name__)


def make_idempotency_key(task_id: str, tool: str, args: dict[str, Any]) -> str:
    raw = f"{task_id}:{tool}:{json.dumps(args, sort_keys=True, default=str)}"
    return hashlib.sha256(raw.encode()).hexdigest()


class TaskRepo:
    """抽象仓储。"""

    async def create_task(self, task: TaskRecord) -> None:
        raise NotImplementedError

    async def update_task_status(self, task_id: str, status: TaskStatus, error: str | None = None) -> None:
        raise NotImplementedError

    async def get_task(self, task_id: str) -> TaskRecord | None:
        raise NotImplementedError

    async def list_tasks_by_session(self, session_id: str, limit: int = 50) -> list[TaskRecord]:
        raise NotImplementedError

    async def list_pending_approvals(self, session_id: str | None = None) -> list[ApprovalRecord]:
        raise NotImplementedError

    async def save_tool_call(self, task_id: str, key: str, record: ToolCallRecord) -> None:
        raise NotImplementedError

    async def list_tool_calls_by_task(self, task_id: str) -> list[ToolCallRecord]:
        raise NotImplementedError

    async def get_tool_call_by_key(self, key: str) -> ToolCallRecord | None:
        raise NotImplementedError

    async def create_approval(self, record: ApprovalRecord) -> int:
        raise NotImplementedError

    async def decide_approval(self, task_id: str, approved: bool, decided_by: str) -> None:
        raise NotImplementedError

    async def get_approval(self, task_id: str) -> ApprovalRecord | None:
        raise NotImplementedError


class InMemoryTaskRepo(TaskRepo):
    """进程内 stub 实现, 用于 dev/test。"""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._tool_calls: dict[str, ToolCallRecord] = {}
        self._tool_calls_by_task: dict[str, dict[str, ToolCallRecord]] = {}
        self._approvals: dict[str, ApprovalRecord] = {}
        self._approval_seq = 0

    async def create_task(self, task: TaskRecord) -> None:
        self._tasks[task.task_id] = task

    async def update_task_status(self, task_id: str, status: TaskStatus, error: str | None = None) -> None:
        t = self._tasks.get(task_id)
        if t:
            self._tasks[task_id] = t.model_copy(update={"status": status, "error": error, "updated_at": datetime.utcnow()})

    async def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    async def list_tasks_by_session(self, session_id: str, limit: int = 50) -> list[TaskRecord]:
        rows = [t for t in self._tasks.values() if t.session_id == session_id]
        rows.sort(key=lambda x: x.created_at, reverse=True)
        return rows[:limit]

    async def list_pending_approvals(self, session_id: str | None = None) -> list[ApprovalRecord]:
        results = [a for a in self._approvals.values() if a.decision == "pending"]
        if session_id:
            results = [a for a in results if a.session_id == session_id]
        return results

    async def save_tool_call(self, task_id: str, key: str, record: ToolCallRecord) -> None:
        self._tool_calls[key] = record
        self._tool_calls_by_task.setdefault(task_id, {})[key] = record

    async def list_tool_calls_by_task(self, task_id: str) -> list[ToolCallRecord]:
        calls = self._tool_calls_by_task.get(task_id, {})
        return list(calls.values())

    async def get_tool_call_by_key(self, key: str) -> ToolCallRecord | None:
        return self._tool_calls.get(key)

    async def create_approval(self, record: ApprovalRecord) -> int:
        self._approval_seq += 1
        record = record.model_copy(update={"id": self._approval_seq})
        self._approvals[record.task_id] = record
        return self._approval_seq

    async def decide_approval(self, task_id: str, approved: bool, decided_by: str) -> None:
        a = self._approvals.get(task_id)
        if a:
            self._approvals[task_id] = a.model_copy(update={
                "decision": "approved" if approved else "rejected",
                "decided_by": decided_by,
                "decided_at": datetime.utcnow(),
            })

    async def get_approval(self, task_id: str) -> ApprovalRecord | None:
        return self._approvals.get(task_id)


class MySqlTaskRepo(TaskRepo):
    """MySQL 实现。"""

    @staticmethod
    def _dict_cursor():
        import aiomysql
        return aiomysql.DictCursor

    async def _conn(self):
        from app.memory.db import get_pool
        pool = await get_pool()
        return await pool.acquire()

    async def _release(self, conn):
        from app.memory.db import get_pool
        pool = await get_pool()
        pool.release(conn)

    async def create_task(self, task: TaskRecord) -> None:
        conn = await self._conn()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO task (task_id, session_id, skill, status) VALUES (%s, %s, %s, %s)",
                    (task.task_id, task.session_id, task.skill, task.status),
                )
        finally:
            await self._release(conn)

    async def update_task_status(self, task_id: str, status: TaskStatus, error: str | None = None) -> None:
        conn = await self._conn()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE task SET status=%s, error=%s WHERE task_id=%s",
                    (status, error, task_id),
                )
        finally:
            await self._release(conn)

    async def get_task(self, task_id: str) -> TaskRecord | None:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                await cur.execute("SELECT * FROM task WHERE task_id=%s", (task_id,))
                row = await cur.fetchone()
                return TaskRecord(**row) if row else None
        finally:
            await self._release(conn)

    async def list_tasks_by_session(self, session_id: str, limit: int = 50) -> list[TaskRecord]:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                await cur.execute(
                    "SELECT * FROM task WHERE session_id=%s ORDER BY created_at DESC LIMIT %s",
                    (session_id, limit),
                )
                rows = await cur.fetchall()
                return [TaskRecord(**r) for r in rows]
        finally:
            await self._release(conn)

    async def list_pending_approvals(self, session_id: str | None = None) -> list[ApprovalRecord]:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                if session_id:
                    await cur.execute(
                        "SELECT * FROM approval WHERE decision='pending' AND session_id=%s ORDER BY created_at DESC",
                        (session_id,),
                    )
                else:
                    await cur.execute("SELECT * FROM approval WHERE decision='pending' ORDER BY created_at DESC")
                rows = await cur.fetchall()
                return [ApprovalRecord(**r) for r in rows]
        finally:
            await self._release(conn)

    async def save_tool_call(self, task_id: str, key: str, record: ToolCallRecord) -> None:
        conn = await self._conn()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO tool_call (task_id, idempotency_key, tool, args, status, result, error, latency_ms) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE status=VALUES(status), result=VALUES(result), error=VALUES(error), latency_ms=VALUES(latency_ms)",
                    (
                        task_id, key, record.tool,
                        json.dumps(record.args, default=str),
                        record.status,
                        json.dumps(record.result, default=str) if record.result else None,
                        record.error, record.latency_ms,
                    ),
                )
        finally:
            await self._release(conn)

    async def get_tool_call_by_key(self, key: str) -> ToolCallRecord | None:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                await cur.execute("SELECT * FROM tool_call WHERE idempotency_key=%s", (key,))
                row = await cur.fetchone()
                if not row:
                    return None
                return ToolCallRecord(
                    tool=row["tool"],
                    args=json.loads(row["args"]) if row["args"] else {},
                    status=row["status"],
                    result=json.loads(row["result"]) if row["result"] else None,
                    error=row["error"],
                    latency_ms=row["latency_ms"],
                )
        finally:
            await self._release(conn)

    async def list_tool_calls_by_task(self, task_id: str) -> list[ToolCallRecord]:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                await cur.execute("SELECT * FROM tool_call WHERE task_id=%s ORDER BY created_at ASC", (task_id,))
                rows = await cur.fetchall()
                return [
                    ToolCallRecord(
                        tool=row["tool"],
                        args=json.loads(row["args"]) if row["args"] else {},
                        status=row["status"],
                        result=json.loads(row["result"]) if row["result"] else None,
                        error=row["error"],
                        latency_ms=row["latency_ms"],
                    )
                    for row in rows
                ]
        finally:
            await self._release(conn)

    async def create_approval(self, record: ApprovalRecord) -> int:
        conn = await self._conn()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO approval (task_id, session_id, tool, args, risk_level, risk_reason, ai_review) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        record.task_id, record.session_id, record.tool,
                        json.dumps(record.args, default=str),
                        record.risk_level, record.risk_reason, record.ai_review,
                    ),
                )
                return cur.lastrowid
        finally:
            await self._release(conn)

    async def decide_approval(self, task_id: str, approved: bool, decided_by: str) -> None:
        conn = await self._conn()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE approval SET decision=%s, decided_by=%s, decided_at=NOW() WHERE task_id=%s AND decision='pending'",
                    ("approved" if approved else "rejected", decided_by, task_id),
                )
        finally:
            await self._release(conn)

    async def get_approval(self, task_id: str) -> ApprovalRecord | None:
        conn = await self._conn()
        try:
            async with conn.cursor(self._dict_cursor()) as cur:
                await cur.execute("SELECT * FROM approval WHERE task_id=%s ORDER BY created_at DESC LIMIT 1", (task_id,))
                row = await cur.fetchone()
                return ApprovalRecord(**row) if row else None
        finally:
            await self._release(conn)


_repo: TaskRepo | None = None


def get_task_repo() -> TaskRepo:
    global _repo
    if _repo is not None:
        return _repo
    s = get_settings()
    if not s.mysql_active():
        _repo = InMemoryTaskRepo()
    else:
        _repo = MySqlTaskRepo()
    return _repo
