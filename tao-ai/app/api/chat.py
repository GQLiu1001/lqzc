import time
import uuid

from fastapi import APIRouter, Depends, Request

from app.audit.schemas import AuditEvent
from app.audit.service import record_audit_event
from app.auth.auth import get_current_user
from app.core.runtime_context import set_session_id, set_user_context
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.user import UserContext
from app.supervisor.service import SupervisorService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
) -> ChatResponse:
    session_id = body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    set_user_context(user_ctx)
    set_session_id(session_id)

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
    return resp
