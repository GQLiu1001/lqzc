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
    """最标准的聊天入口。

    前端一般会直接调用这个接口；
    它内部本身不做业务判断，只是把请求交给总控工作流。
    """
    logger.info(
        "chat.request session_id=%s tenant_id=%s user_id=%s message_len=%s",
        payload.session_id,
        payload.tenant_id,
        payload.user_id,
        len(payload.message or ""),
    )
    # 运行时容器里已经提前把模型、工具、工作流全都装好了。
    runtime = get_runtime_container()
    task_id, session_id, output = await runtime.workflow.run_chat(payload)
    logger.info(
        "chat.response task_id=%s session_id=%s agent=%s status=%s approval=%s",
        task_id,
        session_id,
        output.agent,
        output.status,
        output.requires_approval,
    )
    return ChatResponse.from_agent_output(task_id=task_id, session_id=session_id, output=output)
