"""The main harness loop.

This is the heart of the project.
If you understand this file, you understand the first harness layer:

user message -> model -> tool calls -> tool results -> model -> final answer
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re

from tao_harness.config import settings
from tao_harness.model.ollama_client import OllamaChatClient
from tao_harness.state.sqlite_store import SQLiteStore
from tao_harness.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)
_MODEL_TOKEN = re.compile(r"\b([A-Za-z]{1,6}[0-9]{2,}[A-Za-z0-9-]*)\b")
_INVENTORY_HINTS = (
    "库存",
    "有货",
    "现货",
    "有什么货",
    "有啥货",
    "有什么库存",
    "哪些货",
    "在售",
    "available",
    "in stock",
    "stock",
)


def _preview(value: object, limit: int = 240) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


@dataclass(slots=True)
class ToolEvent:
    tool_name: str
    arguments: dict
    result_preview: str


@dataclass(slots=True)
class AgentRunResult:
    session_id: str
    reply: str
    tool_events: list[ToolEvent]
    steps_used: int


class HarnessAgent:
    """Own the runtime loop, but not the business logic itself."""

    def __init__(
        self,
        model_client: OllamaChatClient,
        tool_registry: ToolRegistry,
        store: SQLiteStore,
        system_prompt_path: Path,
    ) -> None:
        self.model_client = model_client
        self.tool_registry = tool_registry
        self.store = store
        self.system_prompt_path = system_prompt_path

    def _load_system_prompt(self) -> str:
        return self.system_prompt_path.read_text(encoding="utf-8")

    def _build_messages(
        self,
        session_id: str,
        user_message: str,
        context_blocks: list[str] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._load_system_prompt()}
        ]
        if context_blocks:
            for block in context_blocks:
                cleaned = block.strip()
                if cleaned:
                    messages.append({"role": "system", "content": cleaned})

        # The persisted transcript keeps only the clean conversation.
        # Tool chatter lives in tool_logs, not in the visible transcript.
        for item in self.store.list_messages(session_id):
            messages.append({"role": item.role, "content": item.content})

        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _fallback_tool_for_inventory(user_message: str) -> tuple[str, dict[str, object]] | None:
        match = _MODEL_TOKEN.search(user_message)
        if match:
            return ("get_inventory_by_model", {"model": match.group(1).upper()})

        lowered = user_message.lower()
        if any(hint in lowered for hint in _INVENTORY_HINTS):
            return ("search_inventory", {"current": 1, "size": 10})
        return None

    async def run(
        self,
        user_message: str,
        session_id: str | None = None,
        context_blocks: list[str] | None = None,
    ) -> AgentRunResult:
        incoming_session = session_id
        session_id = self.store.ensure_session(session_id)
        logger.info(
            "agent.run.start session_id=%s had_session=%s user=%s",
            session_id,
            incoming_session is not None,
            _preview(user_message, 180),
        )
        messages = self._build_messages(
            session_id,
            user_message,
            context_blocks=context_blocks,
        )
        self.store.append_message(session_id, "user", user_message)

        tool_events: list[ToolEvent] = []
        fallback_used = False

        for step in range(1, settings.max_agent_steps + 1):
            logger.info(
                "agent.step.start session_id=%s step=%s/%s messages=%s",
                session_id,
                step,
                settings.max_agent_steps,
                len(messages),
            )
            turn = await self.model_client.chat(
                messages=messages,
                tools=self.tool_registry.schemas_for_ollama(),
            )

            # We always append the raw assistant message to the live loop.
            # This matters because the next model call needs to know that it
            # previously requested a tool.
            messages.append(turn.message)

            if not turn.tool_calls:
                reply = (turn.content or "").strip()
                if not reply and not fallback_used:
                    fallback = self._fallback_tool_for_inventory(user_message)
                    if fallback is not None:
                        fallback_tool, fallback_args = fallback
                        logger.info(
                            "agent.fallback.tool_invoke session_id=%s step=%s tool=%s args=%s",
                            session_id,
                            step,
                            fallback_tool,
                            _preview(fallback_args),
                        )
                        result = await self.tool_registry.invoke(fallback_tool, fallback_args)
                        logger.info(
                            "agent.fallback.tool_result session_id=%s step=%s tool=%s result=%s",
                            session_id,
                            step,
                            fallback_tool,
                            _preview(result),
                        )
                        tool_events.append(
                            ToolEvent(
                                tool_name=fallback_tool,
                                arguments=fallback_args,
                                result_preview=result[:200],
                            )
                        )
                        self.store.append_tool_call(
                            session_id=session_id,
                            tool_name=fallback_tool,
                            arguments=fallback_args,
                            result_preview=result,
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_name": fallback_tool,
                                "content": result,
                            }
                        )
                        fallback_used = True
                        continue

                if not reply:
                    reply = "我这次没有拿到有效结果，请再试一次，或补充型号/分类后我直接查库存。"
                self.store.append_message(session_id, "assistant", reply)
                logger.info(
                    "agent.run.final session_id=%s step=%s reply=%s",
                    session_id,
                    step,
                    _preview(reply),
                )
                return AgentRunResult(
                    session_id=session_id,
                    reply=reply,
                    tool_events=tool_events,
                    steps_used=step,
                )

            logger.info(
                "agent.step.tool_calls session_id=%s step=%s count=%s names=%s",
                session_id,
                step,
                len(turn.tool_calls),
                [tool_call.name for tool_call in turn.tool_calls],
            )
            for tool_call in turn.tool_calls:
                logger.info(
                    "agent.tool.invoke session_id=%s step=%s tool=%s args=%s",
                    session_id,
                    step,
                    tool_call.name,
                    _preview(tool_call.arguments),
                )
                result = await self.tool_registry.invoke(tool_call.name, tool_call.arguments)
                logger.info(
                    "agent.tool.result session_id=%s step=%s tool=%s result=%s",
                    session_id,
                    step,
                    tool_call.name,
                    _preview(result),
                )
                tool_events.append(
                    ToolEvent(
                        tool_name=tool_call.name,
                        arguments=tool_call.arguments,
                        result_preview=result[:200],
                    )
                )
                self.store.append_tool_call(
                    session_id=session_id,
                    tool_name=tool_call.name,
                    arguments=tool_call.arguments,
                    result_preview=result,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": tool_call.name,
                        "content": result,
                    }
                )

        fallback = (
            f"Stopped after {settings.max_agent_steps} steps to avoid an infinite loop. "
            "Review the tool traces and prompt behavior."
        )
        self.store.append_message(session_id, "assistant", fallback)
        logger.warning(
            "agent.run.max_steps session_id=%s max_steps=%s",
            session_id,
            settings.max_agent_steps,
        )
        return AgentRunResult(
            session_id=session_id,
            reply=fallback,
            tool_events=tool_events,
            steps_used=settings.max_agent_steps,
        )
