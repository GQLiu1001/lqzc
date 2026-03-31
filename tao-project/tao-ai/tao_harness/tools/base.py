"""Core tool abstractions used by the harness."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


ToolHandler = Callable[..., Any] | Callable[..., Awaitable[Any]]


@dataclass(slots=True)
class ToolDefinition:
    """Describe a callable tool in a model-friendly way."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    async def invoke(self, **kwargs: Any) -> str:
        """Execute the tool and normalize the output to text.

        Tool results are sent back to the model as strings.
        We still allow handlers to return dict/list objects because that
        is much easier to work with inside Python; they are serialized here.
        """
        try:
            result = self.handler(**kwargs)
            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            # Tool failure should become part of the conversation, not crash
            # the whole harness. This keeps the loop close to real agent
            # products, where a tool can fail but the model can still decide
            # what to do next.
            return f"Tool `{self.name}` failed: {exc}"
