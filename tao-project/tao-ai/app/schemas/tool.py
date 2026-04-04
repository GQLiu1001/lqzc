"""提供与工具相关的实现。"""

from __future__ import annotations

from pydantic import BaseModel


class ToolTrace(BaseModel):
    """定义工具trace，用于承载当前模块中的核心逻辑。"""
    tool_name: str
    arguments: dict
    result_preview: str
    status: str = "SUCCESS"

