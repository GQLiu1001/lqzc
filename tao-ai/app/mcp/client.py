from __future__ import annotations

import logging
from time import perf_counter

import httpx

from app.core.config import settings
from app.core.trace import trace_in, trace_out

logger = logging.getLogger(__name__)

_http_client: httpx.AsyncClient | None = None


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.mcp_server_url,
            timeout=settings.mcp_timeout_seconds,
        )
    return _http_client


async def call_tool(tool_name: str, arguments: dict) -> dict:
    """Call a tool on the Java MCP Server via Streamable HTTP.

    Returns the parsed JSON result, or an error dict on failure.
    """
    started = perf_counter()
    trace_in("mcp.call_tool", tool_name=tool_name, arguments=arguments)
    client = await _get_http_client()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    try:
        resp = await client.post("", json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            logger.warning("MCP tool %s returned error: %s", tool_name, body["error"])
            result = {
                "success": False,
                "errorCode": "MCP_TOOL_ERROR",
                "message": body["error"].get("message", str(body["error"])),
            }
            trace_out(
                "mcp.call_tool",
                result,
                elapsed_ms=int((perf_counter() - started) * 1000),
                tool_name=tool_name,
                http_status=resp.status_code,
            )
            return result
        result = body.get("result", {})
        content = result.get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            import json as _json

            try:
                parsed = _json.loads(content[0]["text"])
                trace_out(
                    "mcp.call_tool",
                    parsed,
                    elapsed_ms=int((perf_counter() - started) * 1000),
                    tool_name=tool_name,
                    http_status=resp.status_code,
                )
                return parsed
            except (_json.JSONDecodeError, KeyError):
                parsed = {"raw": content[0].get("text", "")}
                trace_out(
                    "mcp.call_tool",
                    parsed,
                    elapsed_ms=int((perf_counter() - started) * 1000),
                    tool_name=tool_name,
                    http_status=resp.status_code,
                )
                return parsed
        trace_out(
            "mcp.call_tool",
            result,
            elapsed_ms=int((perf_counter() - started) * 1000),
            tool_name=tool_name,
            http_status=resp.status_code,
        )
        return result
    except httpx.TimeoutException:
        logger.error("MCP tool %s timed out", tool_name)
        result = {"success": False, "errorCode": "MCP_TIMEOUT", "message": f"{tool_name} 调用超时"}
        trace_out(
            "mcp.call_tool",
            result,
            elapsed_ms=int((perf_counter() - started) * 1000),
            tool_name=tool_name,
            http_status=504,
        )
        return result
    except httpx.HTTPStatusError as exc:
        logger.error("MCP tool %s HTTP error: %s", tool_name, exc)
        result = {"success": False, "errorCode": "MCP_HTTP_ERROR", "message": str(exc)}
        trace_out(
            "mcp.call_tool",
            result,
            elapsed_ms=int((perf_counter() - started) * 1000),
            tool_name=tool_name,
            http_status=exc.response.status_code,
        )
        return result
    except Exception as exc:
        logger.error("MCP tool %s unexpected error: %s", tool_name, exc, exc_info=True)
        result = {"success": False, "errorCode": "MCP_INTERNAL_ERROR", "message": str(exc)}
        trace_out(
            "mcp.call_tool",
            result,
            elapsed_ms=int((perf_counter() - started) * 1000),
            tool_name=tool_name,
        )
        return result


async def close_mcp_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
