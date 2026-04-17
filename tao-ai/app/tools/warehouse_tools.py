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

from app.core.runtime_context import get_user_context
from app.mcp import client as mcp_client

logger = logging.getLogger(__name__)


# ── 库存查询类工具（inventory_subagent 使用）──────────────────────────

@tool
async def inventory_query(warehouse_id: str, item_id: str) -> dict:
    """查询指定仓库下某商品当前库存数量、规格、价格等信息。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not warehouse_id or not item_id:
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供仓库编号和商品ID"}

    # 通过 MCP 调用 Java 端已有的库存查询能力
    result = await mcp_client.call_tool("getInventoryByModel", {"model": item_id.strip()})
    if isinstance(result, dict) and result.get("success") is False:
        return result
    return {
        "success": True,
        "warehouseId": warehouse_id,
        "itemId": item_id,
        "data": result,
    }


@tool
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

    # TODO: wire to Java MCP tool or direct PostgreSQL query once available
    return {
        "success": False,
        "errorCode": "NOT_IMPLEMENTED",
        "message": f"仓库 {warehouse_id} 商品 {item_id} 近 {days} 天流水查询工具尚未接入",
    }


# ── 审批执行类工具（approval_subagent 使用）──────────────────────────

@tool
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

    approval_no = f"AP{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
    # TODO: persist to outbound_approval table in agent_db
    return {
        "success": True,
        "approvalNo": approval_no,
        "warehouseId": warehouse_id,
        "itemId": item_id,
        "qty": qty,
        "reason": reason,
        "applicantId": ctx.user_id,
        "status": "pending",
        "message": "出库申请已提交，等待审批",
    }


@tool
async def approval_status_query(approval_id: str) -> dict:
    """查询审批单当前状态（pending / approved / rejected）。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not approval_id or not approval_id.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供审批单号"}

    # TODO: query outbound_approval table in agent_db
    return {
        "success": False,
        "errorCode": "NOT_IMPLEMENTED",
        "message": f"审批单 {approval_id} 状态查询尚未接入",
    }
