from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(None, alias="sessionId")
    message_id: str | None = Field(None, alias="messageId")
    message: str

    model_config = {"populate_by_name": True}


class ChatResponseData(BaseModel):
    session_id: str = Field(alias="sessionId")
    route: str | None = None
    answer: str | None = None
    tool_calls: list[str] = Field(default_factory=list, alias="toolCalls")
    status: str = "success"
    interrupt: dict | None = None
    error_code: str | None = Field(None, alias="errorCode")
    error_message: str | None = Field(None, alias="errorMessage")

    model_config = {"populate_by_name": True, "by_alias": True}


class ChatResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: ChatResponseData

    model_config = {"populate_by_name": True, "by_alias": True}


class InterruptDecisionRequest(BaseModel):
    session_id: str = Field(alias="sessionId")
    decision: str  # approve / reject
    tool: str
    comment: str | None = None

    model_config = {"populate_by_name": True}
