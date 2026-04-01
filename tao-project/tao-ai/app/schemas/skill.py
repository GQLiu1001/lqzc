from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDescriptor(BaseModel):
    name: str
    domain: str
    retrieval_domain: str
    risk_level: str
    requires_approval: bool
    version: str
    description: str
    tool_hints: list[str] = Field(default_factory=list)


class SkillSelectionTrace(BaseModel):
    skill: str
    route_source: str
    route_reason: str
    route_confidence: float | None = None
