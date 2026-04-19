"""Deep Agents 工具裁剪 middleware.

Deep Agents 默认注入一组内置工具：`task` / `write_todos` / `ls` / `read_file` /
`edit_file` / `glob` / `grep` / `execute`。对于业务域 Agent（Mall 单层、Warehouse 只委派
已注册 subagent）这些工具**全是噪声**——弱模型（如 qwen3:8b）看到 `task` 的长描述会幻觉
调用，并把 Deep Agents 自动注入的 `general-purpose` subagent 的元信息当成答案返回。

本模块提供一个 `ToolBlocklistMiddleware`，在每次 LLM 调用前从 `ModelRequest.tools`
里剔除黑名单工具，彻底杜绝模型看到这些工具签名。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)


def _tool_name(tool: Any) -> str:
    name = getattr(tool, "name", None)
    if isinstance(name, str):
        return name
    if isinstance(tool, dict):
        return str(tool.get("name", ""))
    return ""


class ToolBlocklistMiddleware(AgentMiddleware):
    """Strip banned tools from `ModelRequest.tools` before each LLM call."""

    def __init__(self, *, blocked: set[str]) -> None:
        super().__init__()
        self._blocked = set(blocked)

    def _prune(self, request: ModelRequest) -> None:
        request.tools = [t for t in request.tools if _tool_name(t) not in self._blocked]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        self._prune(request)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        self._prune(request)
        return await handler(request)


DEEPAGENTS_NOISE_TOOLS: set[str] = {
    "write_todos",
    "ls",
    "read_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
}

MALL_BLOCKED_TOOLS: set[str] = DEEPAGENTS_NOISE_TOOLS | {"task"}
WAREHOUSE_BLOCKED_TOOLS: set[str] = DEEPAGENTS_NOISE_TOOLS
