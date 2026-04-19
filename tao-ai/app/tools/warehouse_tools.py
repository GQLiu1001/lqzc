"""Warehouse domain tools — narrow, intent-oriented tools for the WarehouseAgent.

Split into two categories matching the subagent design:
  - Inventory tools (low-risk, query-only)
  - Approval tools (high-risk, execution + interrupt)

All tools read identity from runtime context to enforce permission boundaries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from langchain_core.tools import tool

from app.core.runtime_context import get_session_id, get_user_context
from app.core.trace import traced
from app.mcp import client as mcp_client
from app.tools import rag_tools

logger = logging.getLogger(__name__)


# ── 库存查询类工具（inventory_subagent 使用）──────────────────────────

@tool
@traced("tool.inventory_query")
async def inventory_query(warehouse_id: str, item_id: str) -> dict:
    """查询指定仓库下某商品当前库存数量、规格、价格等信息。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not warehouse_id or not item_id:
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供仓库编号和商品ID"}
    return await mcp_client.call_tool(
        "getWarehouseInventory",
        {"warehouseNum": int(warehouse_id), "itemId": int(item_id)},
    )


@tool
@traced("tool.inventory_log_query")
async def inventory_log_query(
    warehouse_id: str,
    item_id: str,
    days: int = 7,
) -> dict:
    """查询指定仓库下某商品近 N 天库存流水与出入库变化。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not warehouse_id or not item_id:
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供仓库编号和商品ID"}
    return await mcp_client.call_tool(
        "getInventoryLog",
        {"warehouseNum": int(warehouse_id), "itemId": int(item_id), "days": max(1, min(days, 90))},
    )


# ── 审批执行类工具（approval_subagent 使用）──────────────────────────

@tool
@traced("tool.outbound_apply")
async def outbound_apply(
    warehouse_id: str,
    item_id: str,
    qty: int,
    reason: str = "",
) -> dict:
    """提交出库申请，高风险操作，会触发审批中断流程。

    只有 admin 或 warehouse_manager 角色可以发起。
    """
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if ctx.role not in ("admin", "warehouse_manager", "staff"):
        return {
            "success": False,
            "errorCode": "PERMISSION_DENIED",
            "message": f"角色 {ctx.role} 无权发起出库申请",
        }
    if not warehouse_id or not item_id or qty <= 0:
        return {"success": False, "errorCode": "INVALID_PARAM", "message": "仓库、商品、数量参数不完整或非法"}

    role_id = ctx.role_ids[0] if ctx.role_ids else None
    if role_id is None:
        return {"success": False, "errorCode": "MISSING_ROLE", "message": "缺少角色信息，无法提交审批"}

    session_id = get_session_id() or datetime.now(timezone.utc).strftime("sess-%Y%m%d%H%M%S")
    idempotency_key = f"{session_id}:submitOutboundApply:{warehouse_id}:{item_id}:{qty}:{reason.strip()}"

    return await mcp_client.call_tool(
        "submitOutboundApply",
        {
            "warehouseNum": int(warehouse_id),
            "itemId": int(item_id),
            "quantity": qty,
            "reason": reason,
            "operatorUserId": ctx.user_id,
            "roleId": role_id,
            "idempotencyKey": idempotency_key,
        },
    )


@tool
@traced("tool.approval_status_query")
async def approval_status_query(approval_id: str) -> dict:
    """查询审批单当前状态（pending / approved / rejected）。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not approval_id or not approval_id.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供审批单号"}
    return await mcp_client.call_tool("getApprovalStatus", {"approvalId": approval_id.strip()})
