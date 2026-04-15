"""提供与工具相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class ToolTrace(BaseModel):
    """一条工具调用轨迹。"""
    tool_name: str
    arguments: dict
    result_preview: str
    status: str = "SUCCESS"
