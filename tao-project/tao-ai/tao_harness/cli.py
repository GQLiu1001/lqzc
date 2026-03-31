"""Small CLI so the harness can be studied without starting FastAPI."""

from __future__ import annotations

import asyncio

from tao_harness.api.main import build_agent


async def _main() -> None:
    agent = build_agent()
    session_id: str | None = None

    while True:
        try:
            message = input("tao-harness> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not message or message.lower() in {"exit", "quit", "q"}:
            break

        result = await agent.run(message, session_id=session_id)
        session_id = result.session_id

        print(f"[session] {result.session_id}")
        for event in result.tool_events:
            print(f"[tool] {event.tool_name} -> {event.result_preview}")
        print(result.reply)
        print()


if __name__ == "__main__":
    asyncio.run(_main())
