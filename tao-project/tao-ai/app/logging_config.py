from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.observability.metrics import metrics


def setup_logging() -> None:
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
    logging.getLogger("urllib3").setLevel(max(level, logging.WARNING))
    logging.getLogger("httpx").setLevel(max(level, logging.WARNING))
    logging.getLogger(__name__).info(
        "logging.initialized level=%s request_logging=%s",
        level_name,
        settings.enable_request_logging,
    )


class RequestLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = uuid.uuid4().hex[:10]
        request.state.request_id = request_id
        start = time.perf_counter()
        self.logger.info(
            "request.start id=%s method=%s path=%s query=%s",
            request_id,
            request.method,
            request.url.path,
            request.url.query,
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            metrics.observe_http(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_seconds=elapsed_ms / 1000.0,
            )
            self.logger.exception(
                "request.error id=%s method=%s path=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        metrics.observe_http(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=elapsed_ms / 1000.0,
        )
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        self.logger.info(
            "request.end id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
