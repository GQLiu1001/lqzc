"""提供与routes聊天相关的实现。"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.api.deps import get_runtime_container
from app.schemas.api import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """处理聊天请求，并返回标准化响应。"""
    logger.info(
        "chat.request session_id=%s tenant_id=%s user_id=%s message_len=%s",
        payload.session_id,
        payload.tenant_id,
        payload.user_id,
        len(payload.message or ""),
    )
    runtime = get_runtime_container()
    task_id, session_id, output = await runtime.workflow.run_chat(payload)
    logger.info(
        "chat.response task_id=%s session_id=%s agent=%s skill=%s status=%s approval=%s",
        task_id,
        session_id,
        output.agent,
        output.skill,
        output.status,
        output.requires_approval,
    )
    return ChatResponse.from_agent_output(task_id=task_id, session_id=session_id, output=output)
