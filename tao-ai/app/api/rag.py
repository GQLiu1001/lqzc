from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.auth import get_current_user
from app.core.trace import trace_in, trace_out
from app.rag.ingest import ingest_default_corpus
from app.rag.service import get_rag_service
from app.schemas.user import UserContext

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGReindexRequest(BaseModel):
    force_refresh: bool = Field(False, alias="forceRefresh")

    model_config = {"populate_by_name": True}


def _require_staff(user_ctx: UserContext) -> None:
    if user_ctx.user_type != "staff":
        raise HTTPException(status_code=403, detail="当前身份无权查看 RAG 索引信息")


def _require_admin(user_ctx: UserContext) -> None:
    _require_staff(user_ctx)
    if user_ctx.role not in ("admin",):
        raise HTTPException(status_code=403, detail="当前角色无权执行 RAG 重建")


@router.get("/summary")
async def rag_summary(
    user_ctx: UserContext = Depends(get_current_user),
) -> dict:
    _require_staff(user_ctx)
    trace_in(
        "rag.summary",
        user_id=user_ctx.user_id,
        user_type=user_ctx.user_type,
        role=user_ctx.role,
    )
    result = await get_rag_service().corpus_summary()
    trace_out("rag.summary", result)
    return result


@router.post("/reindex")
async def rag_reindex(
    body: RAGReindexRequest,
    user_ctx: UserContext = Depends(get_current_user),
) -> dict:
    _require_admin(user_ctx)
    trace_in(
        "rag.reindex",
        user_id=user_ctx.user_id,
        user_type=user_ctx.user_type,
        role=user_ctx.role,
        force_refresh=body.force_refresh,
    )
    result = await ingest_default_corpus(force_refresh=body.force_refresh)
    trace_out("rag.reindex", result, force_refresh=body.force_refresh)
    return result
