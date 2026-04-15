"""提供与Agentoutput相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.retrieval import Evidence
from app.schemas.tool import ToolTrace


class AgentOutput(BaseModel):
    """工作流产出的标准回答对象。

    它是“工作流内部结果”和“API 返回结果”之间的中间层：
    先统一成这个对象，再由接口层转换成不同响应格式。
    """
    agent: str
    answer: str
    requires_approval: bool = False
    status: str
    risk_level: str = "LOW"
    evidence: list[Evidence] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
