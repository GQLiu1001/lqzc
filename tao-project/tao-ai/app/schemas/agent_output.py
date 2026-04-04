"""提供与Agentoutput相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.retrieval import Evidence
from app.schemas.tool import ToolTrace


class AgentOutput(BaseModel):
    """定义Agentoutput，用于承载当前模块中的核心逻辑。"""
    agent: str
    skill: str
    answer: str
    requires_approval: bool = False
    status: str
    risk_level: str = "LOW"
    evidence: list[Evidence] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
