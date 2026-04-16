"""MCP 客户端封装。

M1: `use_stub_stores=True` 时直接 mock 返回, 不发 HTTP;
M2+: 走 `mcp` 官方 SDK 的 ClientSession 与 Java lqzc-mcp-server 对接。
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if self._settings.use_stub_stores:
            return self._stub(tool, args)
        raise NotImplementedError("真实 MCP 调用将在 M2 接入")

    # --- stub 实现 ---
    def _stub(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        logger.info("mcp_stub call: tool=%s args=%s", tool, args)
        if tool == "order.query":
            oid = args.get("order_id", "unknown")
            return {
                "order_id": oid,
                "status": "待发货",
                "expected_ship_at": "2026-04-16T10:00:00+08:00",
                "items": [{"sku": "SKU-9527", "qty": 2}],
                "_stub": True,
            }
        if tool == "inventory.metric":
            return {
                "warehouse": args.get("warehouse", "A"),
                "sku": args.get("sku", "SKU-9527"),
                "outbound_7d": 1234,
                "_stub": True,
            }
        if tool == "inventory.stock_query":
            return {
                "warehouse": args.get("warehouse", "A"),
                "sku": args.get("sku", "SKU-9527"),
                "available_stock": 245,
                "locked_stock": 17,
                "in_transit": 36,
                "_stub": True,
            }
        if tool == "logistics.query":
            oid = args.get("order_id", "unknown")
            return {
                "order_id": oid,
                "status": "运输中",
                "latest_node": "上海分拨中心已发车",
                "eta": "2026-04-17T18:00:00+08:00",
                "_stub": True,
            }
        if tool == "coupon.query":
            uid = args.get("user_id", "unknown")
            return {
                "user_id": uid,
                "available_count": 2,
                "expired_count": 1,
                "coupons": [
                    {"coupon_id": "CPN-NEW-10", "amount": 10, "status": "available"},
                    {"coupon_id": "CPN-SHIP-5", "amount": 5, "status": "available"},
                    {"coupon_id": "CPN-OLD-8", "amount": 8, "status": "expired"},
                ],
                "_stub": True,
            }
        if tool == "order.refund":
            return {
                "order_id": args.get("order_id", "unknown"),
                "refund_id": "RF-20260416-001",
                "amount": args.get("amount", 0),
                "status": "退款处理中",
                "_stub": True,
            }
        if tool == "coupon.issue":
            return {
                "coupon_id": "CPN-20260416-001",
                "user_id": args.get("user_id", "unknown"),
                "amount": args.get("amount", 10),
                "expire_days": 7,
                "status": "已发放",
                "_stub": True,
            }
        if tool == "order.modify_address":
            return {
                "order_id": args.get("order_id", "unknown"),
                "new_address": args.get("new_address", ""),
                "status": "地址已修改",
                "_stub": True,
            }
        return {"error": f"unknown stub tool {tool}", "_stub": True}


_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
