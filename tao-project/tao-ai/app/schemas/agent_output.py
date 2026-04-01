from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.retrieval import Evidence
from app.schemas.tool import ToolTrace


class AgentOutput(BaseModel):
    agent: str
    skill: str
    answer: str
    requires_approval: bool = False
    status: str
    risk_level: str = "LOW"
    evidence: list[Evidence] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
