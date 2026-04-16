"""审批相关契约。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["high", "medium", "low"]
ApprovalDecision = Literal["pending", "approved", "rejected"]


class PlannedAction(BaseModel):
    """plan 节点规划出的单个动作。"""

    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = "low"
    risk_reason: str = ""


class ApprovalRecord(BaseModel):
    """审批记录 (对应 approval 表)。"""

    id: Optional[int] = None
    task_id: str
    session_id: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = "high"
    risk_reason: str = ""
    ai_review: str = ""
    decision: ApprovalDecision = "pending"
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(BaseModel):
    """前端/管理员提交的审批决定。"""

    approved: bool
    decided_by: str = "admin"
    reason: str = ""


class ApprovalResponse(BaseModel):
    """审批决定后返回给前端的结果。"""

    task_id: str
    decision: ApprovalDecision
    answer: Optional[str] = None
