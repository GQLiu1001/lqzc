from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from langchain_ollama import ChatOllama

from app.core.runtime_context import set_session_id, set_user_context
from app.agents.mall_agent import MallAgent
from app.agents.warehouse_agent import WarehouseAgent
from app.core.config import settings
from app.schemas.chat import ChatResponse, ChatResponseData
from app.schemas.user import UserContext
from app.core.trace import trace_in, trace_out
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
        started = perf_counter()
        trace_in(
            "supervisor.invoke",
            session_id=session_id,
            thread_id=session_id,
            checkpoint_ns="supervisor",
            user_context=user_context,
            message=message[:200],
        )
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

        response = ChatResponse(
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
        trace_out(
            "supervisor.invoke",
            response,
            elapsed_ms=int((perf_counter() - started) * 1000),
            route=response.data.route,
            status=response.data.status,
            tool_calls=response.data.tool_calls,
        )
        return response

    async def resume(
        self,
        session_id: str,
        decision: str,
        tool: str,
        comment: str | None,
    ) -> ChatResponse:
        """Resume an interrupted graph (approval flow)."""
        started = perf_counter()
        trace_in(
            "supervisor.resume",
            session_id=session_id,
            thread_id=session_id,
            checkpoint_ns="supervisor",
            decision=decision,
            tool=tool,
            comment=comment,
        )
        original_user_context = await self._load_original_user_context(session_id)
        if original_user_context is None:
            response = ChatResponse(
                code=404,
                message="not_found",
                data=ChatResponseData(
                    sessionId=session_id,
                    route="warehouse",
                    answer="未找到原始会话上下文，无法恢复审批流程。",
                    status="error",
                    errorCode="SESSION_CONTEXT_NOT_FOUND",
                    errorMessage=f"sessionId={session_id}",
                ),
            )
            trace_out(
                "supervisor.resume",
                response,
                elapsed_ms=int((perf_counter() - started) * 1000),
                status=response.data.status,
                tool=tool,
            )
            return response

        set_user_context(original_user_context)
        set_session_id(session_id)

        result = await self._warehouse_agent.resume(
            session_id=session_id,
            decision=decision,
            tool=tool,
            comment=comment,
        )

        code = 200
        message = "success"
        if result.status == "error":
            code = 400
            message = "error"

        response = ChatResponse(
            code=code,
            message=message,
            data=ChatResponseData(
                sessionId=session_id,
                route="warehouse",
                answer=result.answer,
                toolCalls=result.tool_calls,
                status=result.status,
                interrupt=result.interrupt,
                errorCode=result.error_code,
                errorMessage=result.error_message,
            ),
        )
        trace_out(
            "supervisor.resume",
            response,
            elapsed_ms=int((perf_counter() - started) * 1000),
            status=response.data.status,
            tool=tool,
            decision=decision,
            tool_calls=response.data.tool_calls,
        )
        return response

    async def _load_original_user_context(self, session_id: str) -> UserContext | None:
        snapshot = await self._graph.aget_state(
            {
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "supervisor",
                },
            }
        )
        values = snapshot.values if isinstance(snapshot.values, dict) else {}
        raw_user_context = values.get("user_context")
        if not raw_user_context:
            return None
        return UserContext.model_validate(raw_user_context)
