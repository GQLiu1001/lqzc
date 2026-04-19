import time

from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit.schemas import AuditEvent
from app.audit.service import record_audit_event
from app.auth.auth import get_current_user
from app.core.trace import trace_in, trace_out
from app.schemas.chat import ChatResponse, InterruptDecisionRequest
from app.schemas.user import UserContext
from app.supervisor.service import SupervisorService

router = APIRouter()

_ALLOWED_DECISIONS = {"approve", "reject"}


@router.post("/chat/interrupt/decision", response_model=ChatResponse)
async def submit_decision(
    body: InterruptDecisionRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
) -> ChatResponse:
    trace_in(
        "interrupt.submit_decision",
        session_id=body.session_id,
        decision=body.decision,
        tool=body.tool,
        user_id=user_ctx.user_id,
        role=user_ctx.role,
        comment=body.comment,
    )
    if user_ctx.role not in ("admin",):
        trace_out(
            "interrupt.submit_decision",
            elapsed_ms=0,
            status="forbidden",
            tool=body.tool,
            decision=body.decision,
        )
        raise HTTPException(
            status_code=403,
            detail="当前角色无权执行审批操作",
        )

    if body.decision not in _ALLOWED_DECISIONS:
        trace_out(
            "interrupt.submit_decision",
            elapsed_ms=0,
            status="invalid_request",
            tool=body.tool,
            decision=body.decision,
        )
        raise HTTPException(
            status_code=400,
            detail=f"decision 必须为 {_ALLOWED_DECISIONS} 之一",
        )

    started = time.perf_counter()
    svc = SupervisorService(request.app.state.checkpointer)
    resp = await svc.resume(
        body.session_id, body.decision, body.tool, body.comment,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    data = resp.data
    await record_audit_event(
        AuditEvent(
            session_id=body.session_id,
            message_id=None,
            user_type=user_ctx.user_type,
            user_id=user_ctx.user_id,
            route="warehouse",
            intent=f"approval_{body.decision}",
            tool_name=body.tool,
            tool_args={
                "decision": body.decision,
                "comment": body.comment,
                "tool_calls": data.tool_calls,
            },
            status=data.status,
            error_code=data.error_code,
            latency_ms=latency_ms,
        )
    )
    trace_out(
        "interrupt.submit_decision",
        resp,
        elapsed_ms=latency_ms,
        status=data.status,
        tool=body.tool,
        decision=body.decision,
    )
    return resp
