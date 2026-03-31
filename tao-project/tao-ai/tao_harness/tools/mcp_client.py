"""Small MCP client wrapper for the Java MCP server."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


logger = logging.getLogger(__name__)


def _preview(value: Any, limit: int = 220) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False)
    except TypeError:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


class LQZCMcpClient:
    """Call remote MCP tools over Streamable HTTP.

    We intentionally open a short-lived session per tool call.
    That keeps the integration easy to reason about and avoids coupling
    the existing harness lifecycle to a persistent MCP connection.
    """

    def __init__(self, server_url: str) -> None:
        self.server_url = server_url.rstrip("/")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        logger.info(
            "mcp.call.request url=%s tool=%s args=%s",
            self.server_url,
            tool_name,
            _preview(args),
        )
        try:
            async with streamable_http_client(self.server_url) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=args)
                    normalized = self._normalize_result(result)
                    logger.info(
                        "mcp.call.response tool=%s is_error=%s result=%s",
                        tool_name,
                        result.isError,
                        _preview(normalized),
                    )
                    return normalized
        except Exception:
            logger.exception("mcp.call.failed tool=%s", tool_name)
            raise

    @staticmethod
    def _normalize_result(result: types.CallToolResult) -> Any:
        if result.structuredContent is not None:
            return result.structuredContent

        text_blocks: list[str] = []
        other_blocks: list[dict[str, Any]] = []

        for content in result.content:
            if isinstance(content, types.TextContent):
                text_blocks.append(content.text)
                continue

            if hasattr(content, "model_dump"):
                other_blocks.append(content.model_dump(mode="json"))
            else:
                other_blocks.append({"type": type(content).__name__})

        if other_blocks:
            return {
                "text": "\n".join(text_blocks).strip(),
                "content": other_blocks,
                "is_error": result.isError,
            }
        if len(text_blocks) == 1:
            return LQZCMcpClient._maybe_parse_json(text_blocks[0])
        return LQZCMcpClient._maybe_parse_json("\n".join(text_blocks).strip())

    @staticmethod
    def _maybe_parse_json(value: str) -> Any:
        text = value.strip()
        if not text:
            return text

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
