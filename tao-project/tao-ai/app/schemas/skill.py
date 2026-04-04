"""提供与技能相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDescriptor(BaseModel):
    """定义技能descriptor，用于承载当前模块中的核心逻辑。"""
    name: str
    domain: str
    retrieval_domain: str
    risk_level: str
    requires_approval: bool
    version: str
    description: str
    tool_hints: list[str] = Field(default_factory=list)


class SkillSelectionTrace(BaseModel):
    """定义技能selectiontrace，用于承载当前模块中的核心逻辑。"""
    skill: str
    route_source: str
    route_reason: str
    route_confidence: float | None = None
