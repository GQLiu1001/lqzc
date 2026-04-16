"""Supervisor 主图 — M2。

节点:
  guardrail → router → (customer_service subgraph | warehouse subgraph | handle_other) → summarize

M2 变更:
  - customer_service 作为 compiled subgraph 节点 (共享 state key: user_message, session_id, task_id, sub_report)
  - interrupt 在子图内触发, 父图 checkpointer 自动持久化
  - 新增 session_id / task_id 在 state 中传递
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.supervisor.agent import (
    SUPERVISOR_ROUTER_PROMPT,
    SUPERVISOR_SUMMARIZE_PROMPT,
)
from app.memory.memory_store import get_checkpointer
from app.models.factory import make_chat
from app.schemas.agent_output import RouterDecision, SubAgentReport
from app.workflows.customer_service_workflow import build_customer_service_graph
from app.workflows.qa_react_workflow import build_qa_react_graph
from app.workflows.shared_nodes import guardrail_check
from app.workflows.warehouse_workflow import build_warehouse_graph

logger = logging.getLogger(__name__)


class SupervisorState(TypedDict, total=False):
    # 输入
    user_message: str
    session_id: str
    # 内部流转
    task_id: str
    guardrail_pass: bool
    guardrail_reason: str
    router: RouterDecision
    # 子图共享 key (CustomerServiceState 也有这些)
    rag_hits: list[dict]
    planned_actions: list[dict]
    approval_result: dict
    action_results: list[dict]
    sub_report: Optional[SubAgentReport]
    # 最终输出
    final: str


_cs_subgraph = build_customer_service_graph()
_wh_subgraph = build_warehouse_graph()
_qa_react_subgraph = build_qa_react_graph()


async def _guardrail(state: SupervisorState) -> dict[str, Any]:
    ok, reason = guardrail_check(state.get("user_message", ""))
    return {"guardrail_pass": ok, "guardrail_reason": reason}


async def _router(state: SupervisorState) -> dict[str, Any]:
    if not state.get("guardrail_pass", True):
        return {
            "router": RouterDecision(
                skill="unknown", reason=state.get("guardrail_reason", ""), confidence=1.0
            )
        }
    chat = make_chat(temperature=0.0).with_structured_output(RouterDecision)
    try:
        decision: RouterDecision = await chat.ainvoke(
            [
                SystemMessage(content=SUPERVISOR_ROUTER_PROMPT),
                HumanMessage(content=state["user_message"]),
            ]
        )
    except Exception as exc:
        logger.warning("router structured output failed, fallback to small_talk: %s", exc)
        decision = RouterDecision(skill="small_talk", reason=f"fallback: {exc}", confidence=0.3)
    logger.info("router decided: %s", decision.model_dump())

    task_id = uuid.uuid4().hex[:16]
    return {"router": decision, "task_id": task_id}


async def _handle_other(state: SupervisorState) -> dict[str, Any]:
    skill = state["router"].skill
    if skill == "small_talk":
        report = SubAgentReport(
            skill="small_talk", summary="您好,我是陶选到家智能客服,可以帮您查订单、退款、优惠券等问题。", success=True
        )
    else:
        reason = state.get("guardrail_reason") or state["router"].reason
        report = SubAgentReport(
            skill="unknown", summary=f"暂时无法处理该问题 ({reason}), 将转人工。", success=False
        )
    return {"sub_report": report}


async def _summarize(state: SupervisorState) -> dict[str, Any]:
    report = state.get("sub_report")
    if report is None:
        return {"final": "系统繁忙,请稍后再试。"}
    chat = make_chat(temperature=0.2)
    prompt = SUPERVISOR_SUMMARIZE_PROMPT.format(sub_report=report.model_dump_json())
    resp = await chat.ainvoke([SystemMessage(content=prompt)])
    final = (resp.content or "").strip() if hasattr(resp, "content") else str(resp)
    return {"final": final}


def _route_after_router(state: SupervisorState) -> str:
    skill = state["router"].skill
    if skill == "customer_service":
        return "customer_service"
    if skill == "warehouse":
        return "warehouse"
    if skill == "qa_react":
        return "qa_react"
    return "handle_other"


def build_supervisor_graph(use_checkpointer: bool = True):
    g = StateGraph(SupervisorState)
    g.add_node("guardrail", _guardrail)
    g.add_node("router", _router)
    g.add_node("customer_service", _cs_subgraph)
    g.add_node("warehouse", _wh_subgraph)
    g.add_node("qa_react", _qa_react_subgraph)
    g.add_node("handle_other", _handle_other)
    g.add_node("summarize", _summarize)

    g.add_edge(START, "guardrail")
    g.add_edge("guardrail", "router")
    g.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "customer_service": "customer_service",
            "warehouse": "warehouse",
            "qa_react": "qa_react",
            "handle_other": "handle_other",
        },
    )
    g.add_edge("customer_service", "summarize")
    g.add_edge("warehouse", "summarize")
    g.add_edge("qa_react", "summarize")
    g.add_edge("handle_other", "summarize")
    g.add_edge("summarize", END)

    ckpt = get_checkpointer() if use_checkpointer else None
    return g.compile(checkpointer=ckpt)
