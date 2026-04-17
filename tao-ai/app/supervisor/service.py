from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_ollama import ChatOllama

from app.agents.mall_agent import MallAgent
from app.agents.warehouse_agent import WarehouseAgent
from app.core.config import settings
from app.schemas.chat import ChatResponse, ChatResponseData
from app.schemas.user import UserContext
from app.supervisor.graph import build_graph

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver


class SupervisorService:

    def __init__(self, checkpointer: BaseCheckpointSaver):
        model = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
        )
        self._mall_agent = MallAgent(model=model, checkpointer=checkpointer)
        self._warehouse_agent = WarehouseAgent(model=model, checkpointer=checkpointer)
        self._graph = build_graph(
            checkpointer,
            mall_agent=self._mall_agent,
            warehouse_agent=self._warehouse_agent,
        )

    async def invoke(
        self,
        session_id: str,
        message: str,
        user_context: UserContext,
    ) -> ChatResponse:
        state = {
            "session_id": session_id,
            "message": message,
            "user_context": user_context.model_dump(),
        }

        result = await self._graph.ainvoke(
            state,
            config={
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "supervisor",
                },
            },
        )

        status = result.get("status", "success")
        code = 200
        msg = "success"
        if status == "forbidden":
            code = 403
            msg = "forbidden"

        return ChatResponse(
            code=code,
            message=msg,
            data=ChatResponseData(
                sessionId=result["session_id"],
                route=result.get("route", "fallback"),
                answer=result.get("answer"),
                toolCalls=result.get("tool_calls", []),
                status=status,
                interrupt=result.get("interrupt"),
                errorCode=result.get("error") if status in ("forbidden", "error") else None,
                errorMessage=result.get("answer") if status == "forbidden" else None,
            ),
        )

    async def resume(
        self,
        session_id: str,
        decision: str,
        tool: str,
        comment: str | None,
        user_context: UserContext,
    ) -> ChatResponse:
        """Resume an interrupted graph (approval flow)."""
        # TODO: implement real interrupt resume via LangGraph Command
        return ChatResponse(
            data=ChatResponseData(
                sessionId=session_id,
                route="warehouse",
                answer=f"审批决定已提交: {decision}",
                status="success",
            ),
        )
