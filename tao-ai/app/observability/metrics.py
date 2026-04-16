"""Prometheus 指标定义与埋点辅助函数。"""
from __future__ import annotations

import re

from prometheus_client import Counter, Histogram


_HTTP_REQUESTS_TOTAL = Counter(
    "tao_http_requests_total",
    "Total HTTP requests.",
    labelnames=("method", "path", "status"),
)

_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "tao_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    buckets=(0.01, 0.03, 0.05, 0.1, 0.3, 0.5, 1, 2, 3, 5, 8, 13),
)

_TOOL_CALLS_TOTAL = Counter(
    "tao_tool_calls_total",
    "Total tool calls by status.",
    labelnames=("tool", "status"),
)

_TOOL_LATENCY_SECONDS = Histogram(
    "tao_tool_latency_seconds",
    "Tool execution latency in seconds.",
    labelnames=("tool", "status"),
    buckets=(0.005, 0.01, 0.03, 0.05, 0.1, 0.3, 0.5, 1, 2, 3, 5, 8, 13),
)

_APPROVAL_REQUIRED_TOTAL = Counter(
    "tao_approval_required_total",
    "Total approval-required events.",
)

_APPROVAL_DECISIONS_TOTAL = Counter(
    "tao_approval_decisions_total",
    "Total approval decisions.",
    labelnames=("decision",),
)

_TASK_STATUS_TRANSITIONS_TOTAL = Counter(
    "tao_task_status_transitions_total",
    "Task status transitions.",
    labelnames=("status", "skill"),
)

_RAG_HITS_PER_QUERY = Histogram(
    "tao_rag_hits_per_query",
    "Number of retrieved docs per query.",
    labelnames=("mode",),
    buckets=(0, 1, 2, 3, 4, 5, 8, 12, 20),
)


_HEX_OR_UUID_RE = re.compile(r"^[0-9a-fA-F-]{8,}$")
_DIGITS_RE = re.compile(r"^\d{4,}$")


def _normalize_path(path: str) -> str:
    if not path:
        return "/"

    parts = path.split("/")
    normalized: list[str] = []
    for idx, part in enumerate(parts):
        if idx == 0:
            normalized.append(part)
            continue
        if part and (_HEX_OR_UUID_RE.match(part) or _DIGITS_RE.match(part)):
            normalized.append(":id")
        else:
            normalized.append(part)

    result = "/".join(normalized)
    return result or "/"


def observe_http_request(method: str, path: str, status_code: int, elapsed_seconds: float) -> None:
    normalized_path = _normalize_path(path)
    status = str(status_code)
    _HTTP_REQUESTS_TOTAL.labels(method=method, path=normalized_path, status=status).inc()
    _HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=normalized_path).observe(max(elapsed_seconds, 0.0))


def observe_tool_call(tool: str, status: str, latency_ms: int | None) -> None:
    status_value = status or "unknown"
    _TOOL_CALLS_TOTAL.labels(tool=tool, status=status_value).inc()
    if latency_ms is not None:
        _TOOL_LATENCY_SECONDS.labels(tool=tool, status=status_value).observe(max(latency_ms, 0) / 1000.0)


def inc_approval_required() -> None:
    _APPROVAL_REQUIRED_TOTAL.inc()


def inc_approval_decision(approved: bool) -> None:
    _APPROVAL_DECISIONS_TOTAL.labels(decision="approved" if approved else "rejected").inc()


def inc_task_status(status: str, skill: str) -> None:
    _TASK_STATUS_TRANSITIONS_TOTAL.labels(status=status, skill=skill or "unknown").inc()


def observe_rag_hits(count: int, mode: str) -> None:
    _RAG_HITS_PER_QUERY.labels(mode=mode).observe(max(count, 0))
