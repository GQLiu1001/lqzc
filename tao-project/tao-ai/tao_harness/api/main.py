"""FastAPI entrypoint for the harness."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from tao_harness.config import settings
from tao_harness.core.agent import HarnessAgent
from tao_harness.knowledge.pgvector_store import PgVectorStore
from tao_harness.model.ollama_client import OllamaChatClient
from tao_harness.state.sqlite_store import SQLiteStore
from tao_harness.tools.lqzc_tools import build_default_registry


def _configure_logging() -> None:
    level_name = os.getenv("TAO_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("tao_harness").setLevel(level)


def _preview(value: str, limit: int = 240) -> str:
    single_line = " ".join(value.split())
    return single_line if len(single_line) <= limit else single_line[:limit] + "..."


_configure_logging()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's new message")
    session_id: str | None = Field(default=None, description="Existing session ID if you want to continue a conversation")


class ToolEventPayload(BaseModel):
    tool_name: str
    arguments: dict
    result_preview: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    steps_used: int
    tool_events: list[ToolEventPayload]


class UploadResponse(BaseModel):
    file_id: str
    original_name: str
    local_path: str
    status: str
    chunk_count: int


class UploadFailure(BaseModel):
    detail: str


def build_agent() -> HarnessAgent:
    return HarnessAgent(
        model_client=OllamaChatClient(),
        tool_registry=build_default_registry(),
        store=SQLiteStore(settings.db_path),
        system_prompt_path=settings.prompts_dir / "system.md",
    )


app = FastAPI(title="Tao Harness", version="0.1.0")
agent = build_agent()
try:
    rag_store: PgVectorStore | None = PgVectorStore(
        dsn=settings.postgres_dsn,
        upload_dir=settings.upload_dir,
        ollama_base_url=settings.ollama_base_url,
        embedding_model=settings.ollama_embed_model,
    )
except Exception:
    rag_store = None
    logger.exception("api.rag.init.failed dsn=%s", settings.postgres_dsn)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "rag_status": "ready" if rag_store is not None else "disabled",
        "upload_dir": str(settings.upload_dir),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    logger.info(
        "api.chat.in session_id=%s message=%s",
        payload.session_id or "(new)",
        _preview(payload.message),
    )
    context_blocks: list[str] = []
    if rag_store is not None:
        try:
            chunks, metrics = await rag_store.search(
                query=payload.message,
                session_id=payload.session_id,
                top_k=settings.rag_top_k,
            )
            if chunks:
                context_blocks.append(rag_store.format_context(chunks))
            logger.info(
                "api.chat.rag session_id=%s chunks=%s top_k=%s fill=%.3f recall_proxy=%.3f latency_ms=%s",
                payload.session_id or "(none)",
                len(chunks),
                metrics.top_k_requested,
                metrics.fill_rate_at_k,
                metrics.recall_proxy_at_k,
                metrics.latency_ms,
            )
        except Exception:
            logger.exception("api.chat.rag.failed session_id=%s", payload.session_id or "(none)")

    result = await agent.run(
        payload.message,
        session_id=payload.session_id,
        context_blocks=context_blocks,
    )
    logger.info(
        "api.chat.out session_id=%s steps=%s tool_events=%s reply=%s",
        result.session_id,
        result.steps_used,
        len(result.tool_events),
        _preview(result.reply),
    )
    return ChatResponse(
        session_id=result.session_id,
        reply=result.reply,
        steps_used=result.steps_used,
        tool_events=[
            ToolEventPayload(
                tool_name=item.tool_name,
                arguments=item.arguments,
                result_preview=item.result_preview,
            )
            for item in result.tool_events
        ],
    )


@app.post(
    "/files/upload",
    response_model=UploadResponse,
    responses={500: {"model": UploadFailure}},
)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> UploadResponse:
    if rag_store is None:
        raise HTTPException(status_code=503, detail="RAG 存储未初始化，请先检查 PostgreSQL 连接")
    file_name = file.filename or "uploaded.txt"
    logger.info(
        "api.upload.in session_id=%s filename=%s content_type=%s",
        session_id or "(none)",
        file_name,
        file.content_type or "(unknown)",
    )
    try:
        file_bytes = await file.read()
        result = await rag_store.save_text_file(
            file_bytes=file_bytes,
            original_name=file_name,
            session_id=session_id,
            mime_type=file.content_type,
        )
    except Exception as exc:
        logger.exception("api.upload.failed filename=%s", file_name)
        raise HTTPException(status_code=500, detail=f"文件上传或索引失败: {exc}") from exc
    finally:
        await file.close()

    logger.info(
        "api.upload.out session_id=%s file_id=%s chunks=%s path=%s",
        session_id or "(none)",
        result.file_id,
        result.chunk_count,
        result.local_path,
    )
    return UploadResponse(
        file_id=result.file_id,
        original_name=result.original_name,
        local_path=result.local_path,
        status=result.status,
        chunk_count=result.chunk_count,
    )
