from pydantic import BaseModel, Field


class DomainAgentResult(BaseModel):
    route: str
    answer: str
    tool_calls: list[str] = Field(default_factory=list)
    skill_used: list[str] = Field(default_factory=list)
    status: str = "success"
    interrupt: dict | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw: dict | None = None
