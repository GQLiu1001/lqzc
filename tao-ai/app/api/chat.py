import json
import time
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.audit.schemas import AuditEvent
from app.audit.service import record_audit_event
from app.auth.auth import get_current_user
from app.core.runtime_context import set_session_id, set_user_context
from app.core.trace import trace_in, trace_out
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.user import UserContext
from app.supervisor.service import SupervisorService

router = APIRouter()


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
) -> ChatResponse:
    session_id = body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    set_user_context(user_ctx)
    set_session_id(session_id)
    trace_in(
        "chat",
        session_id=session_id,
        message_id=body.message_id,
        user_id=user_ctx.user_id,
        user_type=user_ctx.user_type,
        role=user_ctx.role,
        message=body.message[:100],
    )

    started = time.perf_counter()
    svc = SupervisorService(request.app.state.checkpointer)
    resp = await svc.invoke(session_id, body.message, user_ctx)
    latency_ms = int((time.perf_counter() - started) * 1000)

    data = resp.data
    first_tool = data.tool_calls[0] if data.tool_calls else None
    await record_audit_event(
        AuditEvent(
            session_id=session_id,
            message_id=body.message_id,
            user_type=user_ctx.user_type,
            user_id=user_ctx.user_id,
            route=data.route,
            tool_name=first_tool,
            tool_args={"tool_calls": data.tool_calls, "message": body.message[:500]},
            status=data.status,
            error_code=data.error_code,
            latency_ms=latency_ms,
        )
    )
    trace_out(
        "chat",
        resp,
        elapsed_ms=latency_ms,
        route=data.route,
        status=data.status,
        tool_calls=data.tool_calls,
    )
    return resp


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
) -> StreamingResponse:
    session_id = body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    set_user_context(user_ctx)
    set_session_id(session_id)
    trace_in(
        "chat.stream",
        session_id=session_id,
        message_id=body.message_id,
        user_id=user_ctx.user_id,
        user_type=user_ctx.user_type,
        role=user_ctx.role,
        message=body.message[:100],
    )

    svc = SupervisorService(request.app.state.checkpointer)

    async def event_source() -> AsyncIterator[str]:
        started = time.perf_counter()
        final_payload: dict | None = None
        try:
            async for ev in svc.astream(session_id, body.message, user_ctx):
                if ev["event"] == "final":
                    final_payload = ev["data"]
                yield _format_sse(ev["event"], ev["data"])
        except Exception as exc:  # pragma: no cover
            yield _format_sse(
                "error",
                {"code": "STREAM_ABORTED", "message": str(exc)},
            )
            yield _format_sse("done", {})

        latency_ms = int((time.perf_counter() - started) * 1000)
        data = (final_payload or {}).get("data") or {}
        tool_calls = data.get("toolCalls", [])
        first_tool = tool_calls[0] if tool_calls else None
        await record_audit_event(
            AuditEvent(
                session_id=session_id,
                message_id=body.message_id,
                user_type=user_ctx.user_type,
                user_id=user_ctx.user_id,
                route=data.get("route"),
                tool_name=first_tool,
                tool_args={
                    "tool_calls": tool_calls,
                    "message": body.message[:500],
                    "stream": True,
                },
                status=data.get("status", "error"),
                error_code=data.get("errorCode"),
                latency_ms=latency_ms,
            )
        )
        trace_out(
            "chat.stream",
            final_payload,
            elapsed_ms=latency_ms,
            route=data.get("route"),
            status=data.get("status"),
            tool_calls=tool_calls,
        )

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
