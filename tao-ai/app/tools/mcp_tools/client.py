"""提供与客户端相关的实现。"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.version import SUPPORTED_PROTOCOL_VERSIONS

from app.config import settings
from app.observability.metrics import metrics


logger = logging.getLogger(__name__)


class MpcClientError(RuntimeError):
    """MCP 调用失败时抛出的统一异常。"""
    pass


class LQZCMcpClient:
    """LQZC 的 MCP 客户端封装。

    某些业务工具不是直接走 HTTP REST，而是通过 MCP 协议远程调用。
    这里负责把这些协议细节封装起来。
    """
    def __init__(self, server_url: str) -> None:
        """初始化LQZCMCP客户端，把运行时依赖和基础状态准备好。"""
        self.server_url = server_url.rstrip("/")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """调用一个远端 MCP 工具。

        整个过程包括：
        - 建立 streamable HTTP 连接
        - 初始化 MCP 会话
        - 调用指定工具
        - 规范化返回结果
        """
        args = arguments or {}
        started_at = time.perf_counter()
        logger.info("mcp.call.start tool=%s server=%s", tool_name, self.server_url)
        try:
            async with streamable_http_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await self._initialize_session(session)
                    result = await session.call_tool(tool_name, arguments=args)
                    elapsed_ms = (time.perf_counter() - started_at) * 1000.0
                    logger.info("mcp.call.end tool=%s duration_ms=%.2f", tool_name, elapsed_ms)
                    metrics.observe_tool_call(
                        tool_name=tool_name,
                        status="SUCCESS",
                        duration_seconds=elapsed_ms / 1000.0,
                    )
                    return self._normalize_result(result)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000.0
            logger.warning(
                "mcp.call.error tool=%s duration_ms=%.2f error=%s",
                tool_name,
                elapsed_ms,
                exc,
            )
            metrics.observe_tool_call(
                tool_name=tool_name,
                status="FAILED",
                duration_seconds=elapsed_ms / 1000.0,
            )
            raise MpcClientError(f"MCP tool `{tool_name}` failed: {exc}") from exc

    @staticmethod
    async def _initialize_session(session: ClientSession) -> None:
        """初始化 MCP 会话并协商协议版本。"""
        configured_protocol = (settings.mcp_protocol_version or "").strip()
        protocol_version = configured_protocol if configured_protocol in SUPPORTED_PROTOCOL_VERSIONS else types.LATEST_PROTOCOL_VERSION

        # 这里显式钉住协议版本，避免客户端和服务端版本不一致时每次都刷告警日志。
        result = await session.send_request(
            types.ClientRequest(
                types.InitializeRequest(
                    params=types.InitializeRequestParams(
                        protocolVersion=protocol_version,
                        capabilities=types.ClientCapabilities(),
                        clientInfo=types.Implementation(name="tao-ai-runtime", version="0.2.0"),
                    )
                )
            ),
            types.InitializeResult,
        )

        if result.protocolVersion not in SUPPORTED_PROTOCOL_VERSIONS:
            raise RuntimeError(f"Unsupported protocol version from server: {result.protocolVersion}")
        logger.info(
            "mcp.initialize protocol_requested=%s protocol_server=%s",
            protocol_version,
            result.protocolVersion,
        )

        await session.send_notification(types.ClientNotification(types.InitializedNotification()))

    @staticmethod
    def _normalize_result(result: types.CallToolResult) -> Any:
        """把 MCP 工具结果规范成项目更容易消费的形式。"""
        if result.structuredContent is not None:
            return result.structuredContent
        texts: list[str] = []
        for content in result.content:
            if isinstance(content, types.TextContent):
                texts.append(content.text)
        joined = "\n".join(texts).strip()
        if not joined:
            return {"is_error": result.isError}
        try:
            return json.loads(joined)
        except json.JSONDecodeError:
            return joined
