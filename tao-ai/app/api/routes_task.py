"""/task: 任务查询 + 审批决定 + 图恢复。

端点:
  GET  /task/{task_id}        — 查任务状态
  GET  /task/pending           — 列出待审批
  POST /task/{task_id}/decide  — 审批/拒绝 → 恢复图执行 → 返回最终回答
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from app.api.deps import get_supervisor_graph
from app.memory.task_repo import get_task_repo
from app.schemas.approval import ApprovalRequest, ApprovalResponse

router = APIRouter(prefix="/task", tags=["task"])
logger = logging.getLogger(__name__)


@router.get("/pending")
async def list_pending(session_id: str | None = None):
    repo = get_task_repo()
    approvals = await repo.list_pending_approvals(session_id)
    return {"approvals": [a.model_dump() for a in approvals]}


@router.get("/{task_id}")
async def get_task(task_id: str):
    repo = get_task_repo()
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    approval = await repo.get_approval(task_id)
    return {
        "task": task.model_dump(),
        "approval": approval.model_dump() if approval else None,
    }


@router.post("/{task_id}/decide")
async def decide_task(task_id: str, req: ApprovalRequest) -> ApprovalResponse:
    """审批决定: 恢复被 interrupt 的图执行。"""
    repo = get_task_repo()
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status != "waiting_approval":
        raise HTTPException(status_code=409, detail=f"task status is {task.status}, not waiting_approval")

    graph = get_supervisor_graph()
    config = {"configurable": {"thread_id": task.session_id}}

    resume_value: dict[str, Any] = {
        "approved": req.approved,
        "decided_by": req.decided_by,
        "reason": req.reason,
    }

    try:
        result = await graph.ainvoke(Command(resume=resume_value), config=config)
        if hasattr(result, "value"):
            final_state = result.value
        elif isinstance(result, dict):
            final_state = result
        else:
            final_state = {}
        answer = final_state.get("final", "")
    except Exception as exc:
        logger.exception("decide_task: graph resume failed for task=%s", task_id)
        await repo.update_task_status(task_id, "failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"graph resume failed: {exc}")

    decision = "approved" if req.approved else "rejected"
    logger.info("decide_task: task=%s decision=%s answer_len=%d", task_id, decision, len(answer))
    return ApprovalResponse(task_id=task_id, decision=decision, answer=answer)
