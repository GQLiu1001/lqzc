from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_eval import router as eval_router
from app.api.routes_files import router as files_router
from app.api.routes_task import router as task_router
from app.config import settings
from app.logging_config import RequestLogMiddleware, setup_logging
from app.observability.metrics import metrics


setup_logging()
app = FastAPI(title=settings.app_name, version="0.2.0")
if settings.enable_request_logging:
    app.add_middleware(RequestLogMiddleware)
if settings.enable_metrics:
    metrics_path = settings.metrics_path if settings.metrics_path.startswith("/") else f"/{settings.metrics_path}"
    app.mount(metrics_path, make_asgi_app())
app.include_router(chat_router)
app.include_router(task_router)
app.include_router(files_router)
app.include_router(admin_router)
app.include_router(eval_router)


@app.on_event("startup")
async def _startup_metrics() -> None:
    if settings.enable_metrics:
        await metrics.startup()


@app.on_event("shutdown")
async def _shutdown_metrics() -> None:
    if settings.enable_metrics:
        await metrics.shutdown()
