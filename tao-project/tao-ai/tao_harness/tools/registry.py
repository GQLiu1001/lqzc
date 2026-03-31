"""Registry for all model-visible tools."""

from __future__ import annotations

from typing import Any

from tao_harness.tools.base import ToolDefinition


class ToolRegistry:
    """Store tool definitions and dispatch calls by name."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def schemas_for_ollama(self) -> list[dict[str, Any]]:
        """Convert internal tools into Ollama's tool schema format."""

        schemas: list[dict[str, Any]] = []
        for tool in self._tools.values():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )
        return schemas

    async def invoke(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool `{name}`"
        return await tool.invoke(**arguments)

