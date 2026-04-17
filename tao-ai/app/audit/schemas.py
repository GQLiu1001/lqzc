from datetime import datetime

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    session_id: str
    message_id: str | None = None
    user_type: str
    user_id: int
    route: str | None = None
    intent: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    status: str = "success"
    error_code: str | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
