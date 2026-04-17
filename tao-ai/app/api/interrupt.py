from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.auth import get_current_user
from app.schemas.chat import ChatResponse, ChatResponseData, InterruptDecisionRequest
from app.schemas.user import UserContext

router = APIRouter()

_ALLOWED_DECISIONS = {"approve", "reject"}


@router.post("/chat/interrupt/decision", response_model=ChatResponse)
async def submit_decision(
    body: InterruptDecisionRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
):
    if user_ctx.role not in ("admin",):
        raise HTTPException(
            status_code=403,
            detail="当前角色无权执行审批操作",
        )

    if body.decision not in _ALLOWED_DECISIONS:
        raise HTTPException(
            status_code=400,
            detail=f"decision 必须为 {_ALLOWED_DECISIONS} 之一",
        )

    checkpointer = request.app.state.checkpointer  # noqa: F841

    # TODO: resume interrupted graph once Supervisor is implemented
    # from app.supervisor.service import SupervisorService
    # svc = SupervisorService(checkpointer)
    # result = await svc.resume(body.session_id, body.decision, body.tool, body.comment, user_ctx)
    # return ChatResponse(data=ChatResponseData(...))

    return ChatResponse(
        data=ChatResponseData(
            sessionId=body.session_id,
            route="warehouse",
            answer=f"审批决定已提交: {body.decision}",
            status="success",
        ),
    )
