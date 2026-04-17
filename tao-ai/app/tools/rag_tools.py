"""Shared RAG search tools used by both MallAgent and WarehouseAgent.

Each tool is a thin wrapper around RAGService, scoped by domain so the
retrieval pipeline applies the correct filters and collection.
"""

from __future__ import annotations

from langchain_core.tools import tool

from app.core.runtime_context import get_session_id, get_user_context
from app.core.trace import traced
from app.rag.service import get_rag_service
from app.schemas.rag import RAGSearchRequest

@tool
@traced("tool.rag.mall_rag_search")
async def mall_rag_search(query: str, scene: str = "general") -> dict:
    """从商城知识库中检索商品 FAQ、运营规则、售后说明。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    ctx = get_user_context()
    result = await get_rag_service().search(
        RAGSearchRequest(
            domain="mall",
            scene=scene,
            query=query,
            user_context=ctx.model_dump() if ctx else {},
            session_id=get_session_id(),
        )
    )
    return result.model_dump(mode="json", by_alias=True)


@tool
@traced("tool.rag.warehouse_rag_search")
async def warehouse_rag_search(query: str, scene: str = "general") -> dict:
    """从仓储知识库中检索仓储 SOP、审批规范、库存规则。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    ctx = get_user_context()
    result = await get_rag_service().search(
        RAGSearchRequest(
            domain="warehouse",
            scene=scene,
            query=query,
            user_context=ctx.model_dump() if ctx else {},
            session_id=get_session_id(),
        )
    )
    return result.model_dump(mode="json", by_alias=True)


@tool
@traced("tool.rag.shared_policy_rag_search")
async def shared_policy_rag_search(query: str) -> dict:
    """从共享规则知识库检索平台统一政策、通用术语、公共审批说明。"""
    if not query or not query.strip():
        return {"success": False, "errorCode": "MISSING_PARAM", "message": "请提供检索问题"}
    ctx = get_user_context()
    result = await get_rag_service().search(
        RAGSearchRequest(
            domain="shared",
            scene="shared_policy",
            query=query,
            user_context=ctx.model_dump() if ctx else {},
            session_id=get_session_id(),
        )
    )
    return result.model_dump(mode="json", by_alias=True)
