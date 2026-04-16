"""/chat: 流式对话接口 (SSE) — M2 增强。

M2 变更:
  - 传入 session_id 到 state
  - 流结束后检测 interrupt → 发送 approval_required 事件
  - 支持 v2 stream API (StreamPart)
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_supervisor_graph
from app.logging_config import new_trace_id
from app.schemas.api import ChatRequest, SSEEvent

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

_TRACKED_NODES = {
    "guardrail", "router", "customer_service", "warehouse", "qa_react", "handle_other", "summarize",
    "retrieve", "plan", "approval_check", "execute", "reflect",
    "prepare", "react",
}


def _sse(event: SSEEvent) -> bytes:
    payload = json.dumps(event.data, ensure_ascii=False, default=str)
    return f"event: {event.event}\ndata: {payload}\n\n".encode("utf-8")


async def _stream(req: ChatRequest, graph) -> AsyncIterator[bytes]:
    trace_id = new_trace_id()
    config = {
        "configurable": {
            "thread_id": req.session_id,
            "user_id": req.user_id or "anonymous",
            "trace_id": trace_id,
        }
    }
    init_state = {"user_message": req.message, "session_id": req.session_id}

    try:
        async for event in graph.astream_events(init_state, config=config, version="v2"):
            etype = event.get("event")
            name = event.get("name")
            if etype == "on_chain_start" and name in _TRACKED_NODES:
                yield _sse(SSEEvent(event="node_start", data={"node": name}))
            elif etype == "on_chain_end" and name in _TRACKED_NODES:
                yield _sse(SSEEvent(event="node_end", data={"node": name}))
            elif etype == "on_tool_start":
                yield _sse(
                    SSEEvent(
                        event="tool_call",
                        data={"tool": name, "input": event.get("data", {}).get("input")},
                    )
                )
            elif etype == "on_tool_end":
                yield _sse(
                    SSEEvent(
                        event="tool_result",
                        data={"tool": name, "output": str(event.get("data", {}).get("output"))[:500]},
                    )
                )

        final_state = await graph.aget_state(config)
        values = final_state.values or {}

        if final_state.next:
            for task in final_state.tasks:
                if task.interrupts:
                    for intr in task.interrupts:
                        yield _sse(SSEEvent(
                            event="approval_required",
                            data={
                                "interrupt_id": intr.id,
                                "trace_id": trace_id,
                                **(intr.value if isinstance(intr.value, dict) else {"value": intr.value}),
                            },
                        ))
            return

        final = values.get("final", "")
        yield _sse(SSEEvent(event="final", data={"text": final, "trace_id": trace_id}))
    except Exception as exc:
        logger.exception("chat stream failed")
        yield _sse(SSEEvent(event="error", data={"message": str(exc), "trace_id": trace_id}))


@router.post("")
async def chat(req: ChatRequest, graph=Depends(get_supervisor_graph)):
    return StreamingResponse(_stream(req, graph), media_type="text/event-stream")
