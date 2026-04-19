from typing import TypedDict


class ChatInputState(TypedDict):
    session_id: str
    message: str
    user_context: dict


class SupervisorState(TypedDict, total=False):
    session_id: str
    message: str
    user_context: dict

    route: str
    route_reason: str
    intent: str
    domain: str
    tool_calls: list[str]
    skill_used: list[str]

    agent_result: dict
    answer: str
    status: str
    error: str | None
    interrupt: dict | None


class ChatOutputState(TypedDict):
    session_id: str
    route: str
    answer: str
    tool_calls: list[str]
    status: str
    interrupt: dict | None
