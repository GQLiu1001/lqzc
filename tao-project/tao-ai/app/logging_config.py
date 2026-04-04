"""提供与日志配置相关的实现。"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.observability.metrics import metrics


def setup_logging() -> None:
    """初始化全局日志配置。

    这里统一设置日志级别、输出格式，并顺手压低第三方库的噪音日志。
    """
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
    """请求日志中间件。

    每个 HTTP 请求都会经过这里，统一记录：
    - 请求开始
    - 请求结束
    - 请求耗时
    - 出错时的异常日志

    同时还会把 HTTP 指标喂给 Prometheus。
    """
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        """初始化requestLOGmiddleware，把运行时依赖和基础状态准备好。"""
        super().__init__(app)
        self.logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """包装一次 HTTP 请求处理流程。"""
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
            # 这里要同时记录错误日志和 HTTP 500 指标，便于排查线上异常。
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
        # 给前端回传 request id 和耗时，方便联动排查。
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
