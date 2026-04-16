"""幂等 Action 执行器。

所有 Tool 调用统一经此模块进出:
  idempotency_key = sha256(task_id : tool : sorted_args)
  先查缓存 → 命中且 status=ok 直接返回 → 否则执行 → 写记录
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.memory.task_repo import get_task_repo, make_idempotency_key
from app.observability.metrics import observe_tool_call
from app.schemas.tool import ToolCallRecord
from app.tools.mcp_tools.lqzc_tools import TOOL_DISPATCH

logger = logging.getLogger(__name__)


async def execute_tool(
    task_id: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolCallRecord:
    """幂等执行单个 Tool。

    返回 ToolCallRecord, 包含 status/result/error/latency_ms。
    """
    repo = get_task_repo()
    key = make_idempotency_key(task_id, tool_name, args)

    existing = await repo.get_tool_call_by_key(key)
    if existing and existing.status == "ok":
        logger.info("action_executor: idempotent hit key=%s tool=%s", key[:12], tool_name)
        observe_tool_call(tool=tool_name, status=existing.status, latency_ms=existing.latency_ms)
        return existing

    tool_fn = TOOL_DISPATCH.get(tool_name)
    if tool_fn is None:
        record = ToolCallRecord(tool=tool_name, args=args, status="error", error=f"unknown tool: {tool_name}")
        await repo.save_tool_call(task_id, key, record)
        observe_tool_call(tool=tool_name, status=record.status, latency_ms=record.latency_ms)
        return record

    start = time.monotonic()
    try:
        result = await tool_fn.ainvoke(args)
        latency = int((time.monotonic() - start) * 1000)
        record = ToolCallRecord(tool=tool_name, args=args, status="ok", result=result, latency_ms=latency)
    except Exception as exc:
        latency = int((time.monotonic() - start) * 1000)
        logger.warning("action_executor: tool=%s failed: %s", tool_name, exc)
        record = ToolCallRecord(tool=tool_name, args=args, status="error", error=str(exc), latency_ms=latency)

    await repo.save_tool_call(task_id, key, record)
    observe_tool_call(tool=tool_name, status=record.status, latency_ms=record.latency_ms)
    logger.info("action_executor: tool=%s status=%s latency=%dms", tool_name, record.status, record.latency_ms or 0)
    return record
