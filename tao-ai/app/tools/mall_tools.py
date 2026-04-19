"""Mall domain tools — narrow, intent-oriented tools for the MallAgent.

All tools that touch user-scoped data read identity from runtime context
instead of accepting user IDs as parameters. This prevents the model from
querying across users.
"""

from __future__ import annotations

import logging

from langchain_core.tools import tool

from app.core.runtime_context import get_user_context
from app.core.trace import traced
from app.mcp import client as mcp_client
from app.tools import rag_tools

logger = logging.getLogger(__name__)


# ── 订单类工具 ─────────────────────────────────────────────────────────

@tool
@traced("tool.my_order_query")
async def my_order_query(limit: int = 5) -> dict:
    """查询当前登录用户最近的订单列表，不允许跨用户查询。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    return await mcp_client.call_tool(
        "getCustomerOrders",
        {"customerId": ctx.user_id, "limit": max(1, min(limit, 20))},
    )


@tool
@traced("tool.order_detail_query")
async def order_detail_query(order_no: str) -> dict:
    """查询当前登录用户指定订单的详情、状态、金额、支付与发货信息。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not order_no or not order_no.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供订单编号"}
    return await mcp_client.call_tool(
        "getCustomerOrderDetail",
        {"customerId": ctx.user_id, "orderNo": order_no.strip()},
    )


@tool
@traced("tool.logistics_trace_query")
async def logistics_trace_query(order_no: str) -> dict:
    """查询当前登录用户指定订单的物流轨迹。"""
    ctx = get_user_context()
    if ctx is None:
        return {"success": False, "errorCode": "NO_USER_CONTEXT", "message": "无法获取当前用户信息"}
    if not order_no or not order_no.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供订单编号"}
    return await mcp_client.call_tool(
        "getCustomerLogisticsTrace",
        {"customerId": ctx.user_id, "orderNo": order_no.strip()},
    )


# ── 商品类工具（通过 MCP 调用 Java 端已有能力）────────────────────────

@tool
@traced("tool.product_consult_query")
async def product_consult_query(model: str | None = None, question: str = "") -> dict:
    """查询商品基础信息、卖点、适用场景、售后规则等。
    可传入商品型号查询库存详情，也可传入自然语言问题做咨询。
    """
    if model and model.strip():
        result = await mcp_client.call_tool("getInventoryByModel", {"model": model.strip()})
        return result
    if question.strip():
        return await rag_tools.mall_rag_search.ainvoke({"query": question, "scene": "product_consult"})
    return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供商品型号或咨询问题"}


@tool
@traced("tool.get_top_sales")
async def get_top_sales() -> dict:
    """查询商城热销榜前五商品，返回商品型号和销量。"""
    return await mcp_client.call_tool("getTopSales", {})


@tool
@traced("tool.search_inventory")
async def search_inventory(
    current: int = 1,
    size: int = 10,
    category: str | None = None,
    surface: str | None = None,
) -> dict:
    """分页查询可售库存商品列表，支持按类别和表面类型筛选。
    适用于"有什么货""有哪些可售瓷砖"这类问题。
    """
    args: dict = {"current": current, "size": size}
    if category:
        args["category"] = category
    if surface:
        args["surface"] = surface
    return await mcp_client.call_tool("searchInventory", args)


# ── 售后规则类工具 ──────────────────────────────────────────────────

@tool
@traced("tool.aftersale_policy_query")
async def aftersale_policy_query(question: str) -> dict:
    """查询售后、退换货、保修、发票等商城规则。
    底层走 RAG 知识库检索。
    """
    if not question or not question.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供售后相关问题"}
    return await rag_tools.mall_rag_search.ainvoke({"query": question, "scene": "aftersale_policy"})


# ── RAG 检索工具 ────────────────────────────────────────────────────

@tool
@traced("tool.mall.mall_rag_search")
async def mall_rag_search(query: str, scene: str = "general") -> dict:
    """从商城知识库中检索商品 FAQ、运营规则、售后说明。"""
    return await rag_tools.mall_rag_search.ainvoke({"query": query, "scene": scene})
