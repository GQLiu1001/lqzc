from __future__ import annotations

import logging

import httpx

from app.core.config import settings

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
            return {
                "success": False,
                "errorCode": "MCP_TOOL_ERROR",
                "message": body["error"].get("message", str(body["error"])),
            }
        result = body.get("result", {})
        content = result.get("content", [])
        if content and isinstance(content, list) and content[0].get("type") == "text":
            import json as _json

            try:
                return _json.loads(content[0]["text"])
            except (_json.JSONDecodeError, KeyError):
                return {"raw": content[0].get("text", "")}
        return result
    except httpx.TimeoutException:
        logger.error("MCP tool %s timed out", tool_name)
        return {"success": False, "errorCode": "MCP_TIMEOUT", "message": f"{tool_name} 调用超时"}
    except httpx.HTTPStatusError as exc:
        logger.error("MCP tool %s HTTP error: %s", tool_name, exc)
        return {"success": False, "errorCode": "MCP_HTTP_ERROR", "message": str(exc)}
    except Exception as exc:
        logger.error("MCP tool %s unexpected error: %s", tool_name, exc, exc_info=True)
        return {"success": False, "errorCode": "MCP_INTERNAL_ERROR", "message": str(exc)}


async def close_mcp_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
