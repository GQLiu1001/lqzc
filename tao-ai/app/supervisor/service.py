from __future__ import annotations

from time import perf_counter
from typing import AsyncIterator, TYPE_CHECKING

from langchain_core.messages import AIMessageChunk
from langchain_ollama import ChatOllama

from app.core.runtime_context import set_session_id, set_user_context
from app.agents.mall_agent import MallAgent
from app.agents.warehouse_agent import WarehouseAgent
from app.core.config import settings
from app.schemas.chat import ChatResponse, ChatResponseData
from app.schemas.user import UserContext
from app.core.trace import trace_error, trace_in, trace_out
from app.supervisor.graph import build_graph

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

_STREAM_SKIP_NODES = {"route", "finalize", "fallback"}


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

    async def astream(
        self,
        session_id: str,
        message: str,
        user_context: UserContext,
    ) -> AsyncIterator[dict]:
        """Stream supervisor execution as a sequence of SSE-friendly events.

        Event shapes:
          - start  {sessionId}
          - route  {route, reason}
          - delta  {text}             # per LLM token from domain agents
          - tool   {name}             # emitted when a domain node reports tool_calls
          - final  ChatResponse body (code/message/data) — same shape as /chat
          - error  {code, message}
          - done   {}
        """
        started = perf_counter()
        trace_in(
            "supervisor.astream",
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
        config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_ns": "supervisor",
            },
        }

        yield {"event": "start", "data": {"sessionId": session_id}}

        final_state: dict = {}
        emitted_tools: set[str] = set()
        try:
            async for mode, chunk in self._graph.astream(
                state,
                config=config,
                stream_mode=["updates", "messages"],
            ):
                if mode == "updates":
                    for node, update in chunk.items():
                        if not isinstance(update, dict):
                            continue
                        if node == "route":
                            yield {
                                "event": "route",
                                "data": {
                                    "route": update.get("route"),
                                    "reason": update.get("route_reason"),
                                },
                            }
                        elif node in ("mall", "warehouse", "fallback"):
                            for tool_name in update.get("tool_calls") or []:
                                if tool_name in emitted_tools:
                                    continue
                                emitted_tools.add(tool_name)
                                yield {"event": "tool", "data": {"name": tool_name}}
                        if node == "finalize":
                            final_state = update
                elif mode == "messages":
                    msg_chunk, meta = chunk
                    if not isinstance(msg_chunk, AIMessageChunk):
                        continue
                    node = (meta or {}).get("langgraph_node", "")
                    if node in _STREAM_SKIP_NODES:
                        continue
                    text = msg_chunk.content or ""
                    if isinstance(text, list):
                        text = "".join(
                            part.get("text", "") if isinstance(part, dict) else str(part)
                            for part in text
                        )
                    if text:
                        yield {"event": "delta", "data": {"text": text}}
        except Exception as exc:
            trace_error(
                "supervisor.astream",
                exc,
                elapsed_ms=int((perf_counter() - started) * 1000),
            )
            yield {
                "event": "error",
                "data": {"code": "INTERNAL_ERROR", "message": str(exc)},
            }
            yield {"event": "done", "data": {}}
            return

        status = final_state.get("status", "success")
        code = 403 if status == "forbidden" else 200
        msg = "forbidden" if status == "forbidden" else "success"
        response = ChatResponse(
            code=code,
            message=msg,
            data=ChatResponseData(
                sessionId=final_state.get("session_id", session_id),
                route=final_state.get("route", "fallback"),
                answer=final_state.get("answer"),
                toolCalls=final_state.get("tool_calls", []),
                status=status,
                interrupt=final_state.get("interrupt"),
                errorCode=final_state.get("error") if status in ("forbidden", "error") else None,
                errorMessage=final_state.get("answer") if status == "forbidden" else None,
            ),
        )
        trace_out(
            "supervisor.astream",
            response,
            elapsed_ms=int((perf_counter() - started) * 1000),
            route=response.data.route,
            status=response.data.status,
            tool_calls=response.data.tool_calls,
        )
        yield {
            "event": "final",
            "data": response.model_dump(mode="json", by_alias=True),
        }
        yield {"event": "done", "data": {}}

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
