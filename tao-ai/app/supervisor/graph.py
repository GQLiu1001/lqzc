from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from app.supervisor.nodes import (
    fallback_node,
    finalize_node,
    route_dispatcher,
    route_node,
)
from app.supervisor.state import ChatInputState, ChatOutputState, SupervisorState

if TYPE_CHECKING:
    from app.agents.mall_agent import MallAgent
    from app.agents.warehouse_agent import WarehouseAgent


def _make_domain_node(agent, route_name: str):
    async def domain_node(state: SupervisorState) -> dict:
        result = await agent.invoke(
            session_id=state["session_id"],
            message=state["message"],
            user_context=state["user_context"],
        )
        return {
            "route": route_name,
            "agent_result": result.model_dump(),
            "answer": result.answer,
            "tool_calls": result.tool_calls,
            "skill_used": result.skill_used,
            "status": result.status,
            "interrupt": result.interrupt,
        }

    return domain_node


def _make_stub(route_name: str):
    async def stub_node(state: SupervisorState) -> dict:
        return {
            "route": route_name,
            "answer": f"[{route_name}_node stub] {state['message']}",
            "tool_calls": [],
            "skill_used": [],
            "status": "success",
            "interrupt": None,
        }

    return stub_node


def build_graph(
    checkpointer,
    *,
    mall_agent: MallAgent | None = None,
    warehouse_agent: WarehouseAgent | None = None,
):
    builder = StateGraph(
        SupervisorState,
        input=ChatInputState,
        output=ChatOutputState,
    )

    builder.add_node("route", route_node)
    builder.add_node(
        "mall",
        _make_domain_node(mall_agent, "mall") if mall_agent else _make_stub("mall"),
    )
    builder.add_node(
        "warehouse",
        _make_domain_node(warehouse_agent, "warehouse") if warehouse_agent else _make_stub("warehouse"),
    )
    builder.add_node("fallback", fallback_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "route")

    builder.add_conditional_edges(
        "route",
        route_dispatcher,
        {
            "mall": "mall",
            "warehouse": "warehouse",
            "fallback": "fallback",
        },
    )

    builder.add_edge("mall", "finalize")
    builder.add_edge("warehouse", "finalize")
    builder.add_edge("fallback", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile(checkpointer=checkpointer)
