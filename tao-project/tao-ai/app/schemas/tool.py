from __future__ import annotations

from pydantic import BaseModel


class ToolTrace(BaseModel):
    tool_name: str
    arguments: dict
    result_preview: str
    status: str = "SUCCESS"

