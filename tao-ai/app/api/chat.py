import uuid

from fastapi import APIRouter, Depends, Request

from app.auth.auth import get_current_user
from app.core.runtime_context import set_session_id, set_user_context
from app.schemas.chat import ChatRequest, ChatResponse, ChatResponseData
from app.schemas.user import UserContext

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user_ctx: UserContext = Depends(get_current_user),
):
    session_id = body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    set_user_context(user_ctx)
    set_session_id(session_id)

    checkpointer = request.app.state.checkpointer

    # TODO: invoke SupervisorService once implemented
    # from app.supervisor.service import SupervisorService
    # svc = SupervisorService(checkpointer)
    # result = await svc.invoke(session_id, body.message, user_ctx)
    # return ChatResponse(data=ChatResponseData(
    #     sessionId=session_id,
    #     route=result.route,
    #     answer=result.answer,
    #     toolCalls=result.tool_calls,
    #     status=result.status,
    #     interrupt=result.interrupt,
    #     errorCode=result.error_code,
    #     errorMessage=result.error_message,
    # ))

    return ChatResponse(
        data=ChatResponseData(
            sessionId=session_id,
            route="echo",
            answer=f"[echo] user_type={user_ctx.user_type}, user_id={user_ctx.user_id}: {body.message}",
            status="success",
        ),
    )
