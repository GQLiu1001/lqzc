"""A very small Ollama chat adapter built on the official HTTP API.

We intentionally keep this file framework-light.
The goal is to make the agent loop easy to understand:

1. build messages
2. send them to Ollama
3. inspect whether the assistant returned tool calls
4. execute those tools
5. send tool results back
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx

from tao_harness.config import settings


logger = logging.getLogger(__name__)


def _preview(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    single_line = " ".join(value.split())
    return single_line if len(single_line) <= limit else single_line[:limit] + "..."


@dataclass(slots=True)
class ToolCall:
    """Normalized tool call returned by the model."""

    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class ChatTurn:
    """Normalized Ollama response."""

    message: dict[str, Any]
    content: str
    thinking: str | None
    tool_calls: list[ToolCall]
    raw: dict[str, Any]


class OllamaChatClient:
    """Thin wrapper around `/api/chat`.

    Ollama already supports native tool calling on supported models.
    We keep the adapter intentionally small so the loop stays readable.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, think: bool | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.think = settings.ollama_think if think is None else think

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ChatTurn:
        last_user_message = ""
        for item in reversed(messages):
            if item.get("role") == "user":
                last_user_message = str(item.get("content", ""))
                break
        logger.info(
            "ollama.chat.request model=%s messages=%s tools=%s last_user=%s",
            self.model,
            len(messages),
            len(tools),
            _preview(last_user_message),
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "think": self.think,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/chat", json=payload)
            if response.is_error:
                logger.error(
                    "ollama.chat.error status=%s body=%s",
                    response.status_code,
                    _preview(response.text),
                )
                # Ollama usually puts the real reason in the body, such as
                # "model not found". Returning that text saves a lot of
                # debugging time during local harness development.
                raise RuntimeError(
                    f"Ollama request failed with {response.status_code}: {response.text}"
                )
            data = response.json()

        message = data.get("message", {})
        tool_calls: list[ToolCall] = []
        for call in message.get("tool_calls", []) or []:
            function = call.get("function", {})
            tool_calls.append(
                ToolCall(
                    name=function.get("name", ""),
                    arguments=function.get("arguments", {}) or {},
                )
            )

        logger.info(
            "ollama.chat.response model=%s content=%s tool_calls=%s tools=%s",
            self.model,
            _preview(message.get("content", "")),
            len(tool_calls),
            [tool.name for tool in tool_calls],
        )

        return ChatTurn(
            message=message,
            content=message.get("content", "") or "",
            thinking=message.get("thinking"),
            tool_calls=tool_calls,
            raw=data,
        )
