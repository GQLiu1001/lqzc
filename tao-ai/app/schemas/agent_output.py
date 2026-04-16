"""Agent 结构化输出契约。"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

SkillName = Literal["customer_service", "warehouse", "qa_react", "small_talk", "unknown"]


class RouterDecision(BaseModel):
    """Supervisor router 的结构化输出。"""

    skill: SkillName
    reason: str = Field(..., description="命中该 skill 的简短理由")
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class SubAgentReport(BaseModel):
    """子图返回给主图的结构化汇报。"""

    skill: SkillName
    summary: str
    citations: list[str] = Field(default_factory=list)
    success: bool = True
