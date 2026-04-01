from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Header, HTTPException

from app.api.deps import get_runtime_container
from app.config import settings
from app.schemas.api import ChatResponse, TaskApproveRequest, TaskExecuteRequest, TaskStatusResponse
from app.schemas.session import SessionDetail, SessionMessage


router = APIRouter(tags=["tasks"])
logger = logging.getLogger(__name__)


def _resolve_approval_token(*, x_approval_token: str | None, authorization: str | None) -> str:
    token = (x_approval_token or "").strip()
    if token:
        return token
    auth_value = (authorization or "").strip()
    if auth_value.lower().startswith("bearer "):
        bearer_token = auth_value[7:].strip()
        if bearer_token:
            return bearer_token
    return ""


@router.post("/tasks/execute", response_model=ChatResponse)
async def execute_task(payload: TaskExecuteRequest) -> ChatResponse:
    logger.info("tasks.execute.request session_id=%s message_len=%s", payload.session_id, len(payload.message or ""))
    runtime = get_runtime_container()
    task_id, session_id, output = await runtime.workflow.run_chat(payload)
    logger.info("tasks.execute.response task_id=%s status=%s", task_id, output.status)
    return ChatResponse.from_agent_output(task_id=task_id, session_id=session_id, output=output)


@router.post("/tasks/approve", response_model=TaskStatusResponse)
def approve_task(
    payload: TaskApproveRequest,
    x_approval_token: str | None = Header(default=None, alias="X-Approval-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> TaskStatusResponse:
    expected_token = settings.approval_admin_token.strip()
    if expected_token:
        provided_token = _resolve_approval_token(
            x_approval_token=x_approval_token,
            authorization=authorization,
        )
        if not provided_token or not secrets.compare_digest(provided_token, expected_token):
            logger.warning("tasks.approve.unauthorized task_id=%s approver=%s", payload.task_id, payload.approver_id)
            raise HTTPException(status_code=401, detail="Unauthorized approval token")
    logger.info(
        "tasks.approve.request task_id=%s action=%s approver=%s",
        payload.task_id,
        payload.approval_action,
        payload.approver_id,
    )
    runtime = get_runtime_container()
    try:
        task = runtime.workflow.approve_task(payload)
    except ValueError as exc:
        if str(exc).startswith("Task status conflict:"):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        logger.warning("tasks.approve.not_found task_id=%s", payload.task_id)
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("tasks.approve.response task_id=%s status=%s", task.task_id, task.status)
    return TaskStatusResponse(task=task)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task(task_id: str) -> TaskStatusResponse:
    runtime = get_runtime_container()
    task = runtime.workflow.get_task(task_id)
    if task is None:
        logger.warning("tasks.get.not_found task_id=%s", task_id)
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("tasks.get.response task_id=%s status=%s", task.task_id, task.status)
    return TaskStatusResponse(task=task)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str) -> SessionDetail:
    runtime = get_runtime_container()
    messages = runtime.workflow.get_session_messages(session_id)
    logger.info("sessions.get.response session_id=%s messages=%s", session_id, len(messages))
    return SessionDetail(
        session_id=session_id,
        messages=[
            SessionMessage(
                role=str(item.get("role", "assistant")),
                content=str(item.get("content", "")),
                created_at=str(item.get("created_at")) if item.get("created_at") else None,
            )
            for item in messages
        ],
    )
