"""Shared RAG search tools used by both MallAgent and WarehouseAgent.

Each tool is a thin wrapper around RAGService, scoped by domain so the
retrieval pipeline applies the correct filters and collection.
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
async def mall_rag_search(query: str, scene: str = "general") -> dict:
    """从商城知识库中检索商品 FAQ、运营规则、售后说明。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    # TODO: wire to RAGService.search(domain="mall", scene=scene, ...)
    return {
        "success": False,
        "errorCode": "NOT_IMPLEMENTED",
        "no_hit": True,
        "message": "商城知识库检索尚未接入",
        "query": query,
        "scene": scene,
    }


@tool
async def warehouse_rag_search(query: str, scene: str = "general") -> dict:
    """从仓储知识库中检索仓储 SOP、审批规范、库存规则。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    # TODO: wire to RAGService.search(domain="warehouse", scene=scene, ...)
    return {
        "success": False,
        "errorCode": "NOT_IMPLEMENTED",
        "no_hit": True,
        "message": "仓储知识库检索尚未接入",
        "query": query,
        "scene": scene,
    }


@tool
async def shared_policy_rag_search(query: str) -> dict:
    """从共享规则知识库检索平台统一政策、通用术语、公共审批说明。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    # TODO: wire to RAGService.search(domain="shared", ...)
    return {
        "success": False,
        "errorCode": "NOT_IMPLEMENTED",
        "no_hit": True,
        "message": "共享知识库检索尚未接入",
        "query": query,
    }
