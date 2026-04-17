import uuid

from fastapi import APIRouter, Depends, Request

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

    svc = SupervisorService(request.app.state.checkpointer)
    return await svc.invoke(session_id, body.message, user_ctx)
