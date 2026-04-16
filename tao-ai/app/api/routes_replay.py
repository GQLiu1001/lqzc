"""/replay: trace 回放与可视化数据接口。

端点:
  GET /replay/session/{session_id}  — 会话级执行历史（state snapshots + task timeline）
  GET /replay/task/{task_id}        — 任务级执行历史（自动反查 session_id）
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import get_supervisor_graph
from app.memory.task_repo import get_task_repo

router = APIRouter(prefix="/replay", tags=["replay"])
logger = logging.getLogger(__name__)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump())
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    return str(value)


async def _build_session_trace(session_id: str, limit: int = 50) -> dict[str, Any]:
    graph = get_supervisor_graph()
    config = {"configurable": {"thread_id": session_id}}

    snapshots: list[dict[str, Any]] = []
    try:
        async for snap in graph.aget_state_history(config=config, limit=limit):
            values = snap.values if isinstance(snap.values, dict) else {}
            router = values.get("router")
            router_skill = getattr(router, "skill", None) if router is not None else None
            if router_skill is None and isinstance(router, dict):
                router_skill = router.get("skill")

            planned = values.get("planned_actions", [])
            rag_hits = values.get("rag_hits", [])
            approval_result = values.get("approval_result", {})

            snapshots.append(
                {
                    "created_at": getattr(snap, "created_at", None),
                    "next_nodes": list(getattr(snap, "next", ()) or ()),
                    "router_skill": router_skill,
                    "guardrail_pass": values.get("guardrail_pass"),
                    "planned_tools": [a.get("tool", "") for a in planned if isinstance(a, dict)],
                    "rag_doc_ids": [h.get("doc_id", "") for h in rag_hits if isinstance(h, dict)],
                    "approval_method": approval_result.get("method") if isinstance(approval_result, dict) else None,
                    "final": values.get("final"),
                    "interrupt_count": len(getattr(snap, "interrupts", ()) or ()),
                    "metadata": _jsonable(getattr(snap, "metadata", None)),
                }
            )
    except Exception as exc:
        logger.warning("replay: failed to load state history for session=%s: %s", session_id, exc)

    repo = get_task_repo()
    tasks = await repo.list_tasks_by_session(session_id, limit=limit)
    task_timeline = []
    for task in tasks:
        approval = await repo.get_approval(task.task_id)
        tool_calls = await repo.list_tool_calls_by_task(task.task_id)
        task_timeline.append(
            {
                "task": task.model_dump(),
                "approval": approval.model_dump() if approval else None,
                "tool_calls": [t.model_dump() for t in tool_calls],
            }
        )

    # get_state_history 常见返回顺序是从新到旧，这里反转为时间正序便于前端画时间线
    snapshots.reverse()
    task_timeline.reverse()

    status_counts: dict[str, int] = {}
    for row in task_timeline:
        status = row["task"].get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "session_id": session_id,
        "summary": {
            "snapshot_count": len(snapshots),
            "task_count": len(task_timeline),
            "task_status_counts": status_counts,
        },
        "snapshots": snapshots,
        "tasks": task_timeline,
    }


@router.get("/session/{session_id}")
async def replay_session(session_id: str, limit: int = 50):
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be in 1..200")
    return await _build_session_trace(session_id=session_id, limit=limit)


@router.get("/task/{task_id}")
async def replay_task(task_id: str, limit: int = 50):
    repo = get_task_repo()
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    payload = await _build_session_trace(session_id=task.session_id, limit=limit)
    payload["focus_task_id"] = task_id
    return payload

