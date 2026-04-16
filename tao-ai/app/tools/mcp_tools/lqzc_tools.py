"""Java lqzc 侧业务工具的 LangChain 封装。

当前包含两类:
  - 查询类工具: order / inventory / logistics / coupon
  - 写操作工具: refund / issue_coupon / modify_address (高风险)
"""
from __future__ import annotations

from langchain_core.tools import tool

from app.tools.mcp_tools.client import get_mcp_client


@tool("order_query", return_direct=False)
async def order_query(order_id: str) -> dict:
    """按订单号查询订单状态、预计发货时间、商品明细。"""
    return await get_mcp_client().call("order.query", {"order_id": order_id})


@tool("inventory_metric", return_direct=False)
async def inventory_metric(warehouse: str, sku: str) -> dict:
    """查询指定仓库 + SKU 近 7 天出库量。"""
    return await get_mcp_client().call(
        "inventory.metric", {"warehouse": warehouse, "sku": sku}
    )


@tool("inventory_stock_query", return_direct=False)
async def inventory_stock_query(warehouse: str, sku: str) -> dict:
    """查询仓库 + SKU 的库存快照（可用/锁定/在途）。"""
    return await get_mcp_client().call(
        "inventory.stock_query", {"warehouse": warehouse, "sku": sku}
    )


@tool("logistics_query", return_direct=False)
async def logistics_query(order_id: str) -> dict:
    """按订单号查询物流轨迹与当前节点。"""
    return await get_mcp_client().call(
        "logistics.query", {"order_id": order_id}
    )


@tool("coupon_query", return_direct=False)
async def coupon_query(user_id: str) -> dict:
    """查询用户可用/已过期优惠券概览。"""
    return await get_mcp_client().call(
        "coupon.query", {"user_id": user_id}
    )


@tool("refund_order", return_direct=False)
async def refund_order(order_id: str, amount: float, reason: str = "") -> dict:
    """对指定订单发起退款 (高风险操作, 需审批)。"""
    return await get_mcp_client().call(
        "order.refund", {"order_id": order_id, "amount": amount, "reason": reason}
    )


@tool("issue_coupon", return_direct=False)
async def issue_coupon(user_id: str, amount: float, reason: str = "") -> dict:
    """向用户发放补偿优惠券 (高风险操作, 需审批)。"""
    return await get_mcp_client().call(
        "coupon.issue", {"user_id": user_id, "amount": amount, "reason": reason}
    )


@tool("modify_address", return_direct=False)
async def modify_address(order_id: str, new_address: str) -> dict:
    """修改订单收货地址 (高风险操作, 需审批)。"""
    return await get_mcp_client().call(
        "order.modify_address", {"order_id": order_id, "new_address": new_address}
    )


ALL_MCP_TOOLS = [
    order_query,
    inventory_metric,
    inventory_stock_query,
    logistics_query,
    coupon_query,
    refund_order,
    issue_coupon,
    modify_address,
]

HIGH_RISK_TOOLS = {"refund_order", "issue_coupon", "modify_address"}
LOW_RISK_TOOLS = {
    "order_query",
    "inventory_metric",
    "inventory_stock_query",
    "logistics_query",
    "coupon_query",
}

TOOL_DISPATCH = {
    "order_query": order_query,
    "inventory_metric": inventory_metric,
    "inventory_stock_query": inventory_stock_query,
    "logistics_query": logistics_query,
    "coupon_query": coupon_query,
    "refund_order": refund_order,
    "issue_coupon": issue_coupon,
    "modify_address": modify_address,
}
