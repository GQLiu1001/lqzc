from __future__ import annotations

import inspect
import json
import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable

from pydantic import BaseModel

from app.core.runtime_context import get_session_id

TRACE_LOGGER_NAME = "taoai.trace"
TRACE_TEXT_LIMIT = 500
TRACE_KEYS_LIMIT = 12

_MISSING = object()
_SENSITIVE_TOKENS = ("password", "passwd", "secret", "token", "authorization", "cookie")
_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger(TRACE_LOGGER_NAME).setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("pymilvus").setLevel(logging.WARNING)
    _LOGGING_CONFIGURED = True


def trace_in(name: str, **kwargs: Any) -> None:
    _log_trace("→", name, kwargs, level="info")


def trace_out(
    name: str,
    result: Any = _MISSING,
    elapsed_ms: int | None = None,
    **kwargs: Any,
) -> None:
    fields: dict[str, Any] = {}
    if elapsed_ms is not None:
        fields["elapsed"] = elapsed_ms
    if result is not _MISSING:
        fields.update(_extract_result_fields(result))
    fields.update(kwargs)
    _log_trace("←", name, fields, level="info")


def trace_error(
    name: str,
    error: Exception,
    elapsed_ms: int | None = None,
    **kwargs: Any,
) -> None:
    fields: dict[str, Any] = {}
    if elapsed_ms is not None:
        fields["elapsed"] = elapsed_ms
    fields["error"] = f"{type(error).__name__}: {_truncate_text(error)}"
    fields.update(kwargs)
    _log_trace("✖", name, fields, level="error")


def traced(
    name: str | None = None,
    *,
    in_fn: Callable[..., dict[str, Any] | None] | None = None,
    out_fn: Callable[..., dict[str, Any] | None] | None = None,
):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        trace_name = name or func.__qualname__
        signature = inspect.signature(func)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            incoming = _bound_arguments(signature, *args, **kwargs)
            incoming.update(_safe_call(in_fn, *args, **kwargs))
            trace_in(trace_name, **incoming)

            started = perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                trace_error(
                    trace_name,
                    exc,
                    elapsed_ms=int((perf_counter() - started) * 1000),
                    **_safe_call(out_fn, None, *args, **kwargs),
                )
                raise

            trace_out(
                trace_name,
                result=result,
                elapsed_ms=int((perf_counter() - started) * 1000),
                **_safe_call(out_fn, result, *args, **kwargs),
            )
            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            incoming = _bound_arguments(signature, *args, **kwargs)
            incoming.update(_safe_call(in_fn, *args, **kwargs))
            trace_in(trace_name, **incoming)

            started = perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                trace_error(
                    trace_name,
                    exc,
                    elapsed_ms=int((perf_counter() - started) * 1000),
                    **_safe_call(out_fn, None, *args, **kwargs),
                )
                raise

            trace_out(
                trace_name,
                result=result,
                elapsed_ms=int((perf_counter() - started) * 1000),
                **_safe_call(out_fn, result, *args, **kwargs),
            )
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _log_trace(direction: str, name: str, fields: dict[str, Any], level: str) -> None:
    configure_logging()
    logger = logging.getLogger(TRACE_LOGGER_NAME)
    prepared = _prepare_fields(fields)
    message = f"[TRACE]{direction} {name}"
    if prepared:
        message += " " + " ".join(
            f"{key}={_format_value(key, value)}" for key, value in prepared.items()
        )
    getattr(logger, level)(message)


def _prepare_fields(fields: dict[str, Any]) -> dict[str, Any]:
    prepared: dict[str, Any] = {}
    session_id = get_session_id()
    if session_id and "session_id" not in fields and "sessionId" not in fields:
        prepared["session_id"] = _summarize_value(session_id, "session_id")

    for key, value in fields.items():
        if value is None:
            continue
        prepared[key] = _summarize_value(value, key)
    return prepared


def _extract_result_fields(result: Any) -> dict[str, Any]:
    payload = _to_payload(result)

    if isinstance(payload, dict):
        summary = _summarize_mapping(payload)
        return summary if summary else {"keys": _summarize_keys(payload)}

    if isinstance(payload, (list, tuple, set)):
        items = list(payload)
        return {"items": len(items)}

    if payload is None:
        return {}

    return {"result": _summarize_value(payload)}


def _summarize_value(value: Any, key: str | None = None) -> Any:
    if _is_sensitive_key(key):
        return "[REDACTED]"

    payload = _to_payload(value)

    if isinstance(payload, dict):
        return _summarize_mapping(payload)

    if isinstance(payload, (list, tuple, set)):
        items = list(payload)
        if not items:
            return []
        if len(items) == 1 and isinstance(_to_payload(items[0]), dict):
            return {
                "items": 1,
                "first": _summarize_mapping(_to_payload(items[0])),
            }
        if len(items) <= 6 and all(_is_simple(_to_payload(item)) for item in items):
            return [_summarize_value(item) for item in items]
        return {"items": len(items)}

    if isinstance(payload, str):
        return _truncate_text(payload)

    if _is_simple(payload):
        return payload

    return _truncate_text(payload)


def _summarize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"keys": _summarize_keys(mapping)}
    reserved_keys = {
        "data",
        "success",
        "code",
        "message",
        "route",
        "status",
        "errorCode",
        "error_code",
        "errorMessage",
        "error_message",
        "tool",
        "tool_name",
        "toolName",
        "search_mode",
        "searchMode",
        "mode",
        "no_hit",
        "noHit",
        "available",
        "indexed",
        "documents",
        "chunks",
        "syncSkipped",
        "sync_skipped",
        "retrieved_docs_count",
        "hits",
        "toolCalls",
        "tool_calls",
        "skillUsed",
        "skill_used",
        "interrupt",
        "domains",
    }

    views = [mapping]
    nested = mapping.get("data")
    if isinstance(nested, dict):
        views.append(nested)

    for view in views:
        _assign_first(summary, "success", view, "success")
        _assign_first(summary, "code", view, "code")
        _assign_first(summary, "message", view, "message")
        _assign_first(summary, "route", view, "route")
        _assign_first(summary, "status", view, "status")
        _assign_first(summary, "error_code", view, "errorCode", "error_code")
        _assign_first(summary, "error_message", view, "errorMessage", "error_message")
        _assign_first(summary, "tool", view, "tool", "tool_name", "toolName")
        _assign_first(summary, "mode", view, "search_mode", "searchMode", "mode")
        _assign_first(summary, "no_hit", view, "no_hit", "noHit")
        _assign_first(summary, "available", view, "available")
        _assign_first(summary, "indexed", view, "indexed")
        _assign_first(summary, "documents", view, "documents")
        _assign_first(summary, "chunks", view, "chunks")
        _assign_first(summary, "sync_skipped", view, "syncSkipped", "sync_skipped")

        if "retrieved_docs_count" in view and "hits" not in summary:
            summary["hits"] = view["retrieved_docs_count"]
        elif "hits" in view and "hits" not in summary:
            hits = view["hits"]
            summary["hits"] = len(hits) if isinstance(hits, list) else hits

        if "toolCalls" in view and "tool_calls" not in summary:
            summary["tool_calls"] = _summarize_value(view["toolCalls"], "toolCalls")
        elif "tool_calls" in view and "tool_calls" not in summary:
            summary["tool_calls"] = _summarize_value(view["tool_calls"], "tool_calls")

        if "skill_used" in view and "skill_used" not in summary:
            summary["skill_used"] = _summarize_value(view["skill_used"], "skill_used")
        elif "skillUsed" in view and "skill_used" not in summary:
            summary["skill_used"] = _summarize_value(view["skillUsed"], "skillUsed")

        interrupt = view.get("interrupt")
        if isinstance(interrupt, dict):
            if "interrupt_tool" not in summary and interrupt.get("tool"):
                summary["interrupt_tool"] = interrupt.get("tool")
            if "interrupt_id" not in summary and interrupt.get("id"):
                summary["interrupt_id"] = interrupt.get("id")

        domains = view.get("domains")
        if isinstance(domains, dict) and "domains" not in summary:
            summary["domains"] = sorted(domains.keys())

    extra_fields = 0
    for key, value in mapping.items():
        if key in reserved_keys or key in summary or _is_sensitive_key(key):
            continue
        payload = _to_payload(value)
        if isinstance(payload, dict):
            continue
        if isinstance(payload, (list, tuple, set)):
            items = list(payload)
            if len(items) > 6 or not all(_is_simple(_to_payload(item)) for item in items):
                continue
        if not _is_simple(payload) and not isinstance(payload, (list, tuple, set)):
            continue
        summary[key] = _summarize_value(value, key)
        extra_fields += 1
        if extra_fields >= 6:
            break

    return summary


def _summarize_keys(mapping: dict[str, Any]) -> list[str]:
    keys = list(mapping.keys())
    if len(keys) <= TRACE_KEYS_LIMIT:
        return keys
    remaining = len(keys) - TRACE_KEYS_LIMIT
    return [*keys[:TRACE_KEYS_LIMIT], f"+{remaining}"]


def _assign_first(summary: dict[str, Any], target: str, source: dict[str, Any], *keys: str) -> None:
    if target in summary:
        return
    for key in keys:
        if key in source:
            summary[target] = _summarize_value(source[key], key)
            return


def _bound_arguments(signature: inspect.Signature, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        bound = signature.bind_partial(*args, **kwargs)
    except TypeError:
        return {}
    return {
        key: value
        for key, value in bound.arguments.items()
        if key not in {"self", "cls"}
    }


def _safe_call(func: Callable[..., dict[str, Any] | None] | None, *args: Any, **kwargs: Any) -> dict[str, Any]:
    if func is None:
        return {}
    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        logging.getLogger(TRACE_LOGGER_NAME).debug("trace helper failed: %s", exc)
        return {}
    return result or {}


def _to_payload(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    return value


def _format_value(key: str, value: Any) -> str:
    if key == "elapsed":
        return f"{int(value)}ms"
    return json.dumps(value, ensure_ascii=False)


def _truncate_text(value: Any) -> str:
    text = str(value).replace("\n", "\\n")
    if len(text) <= TRACE_TEXT_LIMIT:
        return text
    return text[: TRACE_TEXT_LIMIT - 3] + "..."


def _is_sensitive_key(key: str | None) -> bool:
    if not key:
        return False
    lowered = key.lower()
    return any(token in lowered for token in _SENSITIVE_TOKENS)


def _is_simple(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


__all__ = [
    "configure_logging",
    "trace_error",
    "trace_in",
    "trace_out",
    "traced",
]
