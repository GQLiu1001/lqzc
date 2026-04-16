"""FastAPI 入口 — M2。"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.routes_chat import router as chat_router
from app.api.routes_eval import router as eval_router
from app.api.routes_replay import router as replay_router
from app.api.routes_task import router as task_router
from app.config import get_settings
from app.logging_config import setup_logging
from app.observability.metrics import observe_http_request

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    setup_logging(s.log_level)
    logger.info(
        "tao-ai starting env=%s stub=%s chat_model=%s",
        s.app_env, s.use_stub_stores, s.ollama_chat_model,
    )

    if s.mysql_active():
        from app.memory.db import get_pool
        from app.memory.memory_store import setup_checkpointer
        await get_pool()
        await setup_checkpointer()

    yield

    if s.mysql_active():
        from app.memory.db import close_pool
        from app.memory.memory_store import close_checkpointer
        await close_checkpointer()
        await close_pool()

    logger.info("tao-ai stopping")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="tao-ai", version="0.4.0", lifespan=lifespan)
    app.include_router(chat_router)
    app.include_router(task_router)
    app.include_router(eval_router)
    app.include_router(replay_router)

    if s.enable_metrics:
        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            start = time.monotonic()
            status_code = 500
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                observe_http_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    elapsed_seconds=time.monotonic() - start,
                )

        @app.get(s.metrics_path, include_in_schema=False)
        async def metrics():
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    return app


app = create_app()
