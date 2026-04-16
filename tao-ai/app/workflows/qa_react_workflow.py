"""QA ReAct 子图 (SubAgent) — M7。

基于 `langgraph.prebuilt.create_react_agent` 的 ReAct 循环
(Thought → Action → Observation → ... → Final Answer)。

与 customer_service / warehouse 子图形成对比:
  - 固定管线子图: retrieve → plan → (approval) → execute → reflect (流程明确, 有审批)
  - ReAct 子图:   LLM 自主决定何时 / 调用哪个工具, 直到产出终态回答 (灵活)

仅绑定只读工具, 避免在 ReAct 自由循环中误触发写操作;
写操作仍交给 customer_service 的三级审批链路。

本子图以 StateGraph 包了一层 prebuilt agent:
  prepare (建 task 记录) → react (调用 prebuilt agent) → END
目的是保持与其它子图一致的 state key (task_id / sub_report) 便于 Supervisor 汇总。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from app.agents.qa_react.agent import QA_REACT_SYSTEM_PROMPT
from app.memory.task_repo import get_task_repo
from app.models.factory import make_chat
from app.observability.metrics import inc_task_status, observe_tool_call
from app.schemas.agent_output import SubAgentReport
from app.schemas.task import TaskRecord
from app.tools.mcp_tools.lqzc_tools import (
    coupon_query,
    inventory_metric,
    inventory_stock_query,
    logistics_query,
    order_query,
)
from app.tools.rag_tools.retriever_tool import rag_search

logger = logging.getLogger(__name__)

READONLY_TOOLS = [
    rag_search,
    order_query,
    inventory_metric,
    inventory_stock_query,
    logistics_query,
    coupon_query,
]

_REACT_MAX_ITERATIONS = 6


class QaReactState(TypedDict, total=False):
    user_message: str
    session_id: str
    task_id: str
    react_tools_used: list[str]
    react_iterations: int
    sub_report: SubAgentReport


_react_agent_cache = None


def _get_react_agent():
    global _react_agent_cache
    if _react_agent_cache is None:
        llm = make_chat(temperature=0.1)
        _react_agent_cache = create_react_agent(
            llm,
            tools=READONLY_TOOLS,
            prompt=QA_REACT_SYSTEM_PROMPT,
            name="qa_react_agent",
        )
    return _react_agent_cache


async def _prepare(state: QaReactState) -> dict[str, Any]:
    task_id = state.get("task_id") or uuid.uuid4().hex[:16]
    repo = get_task_repo()
    await repo.create_task(
        TaskRecord(
            task_id=task_id,
            session_id=state.get("session_id", ""),
            skill="qa_react",
            status="running",
        )
    )
    inc_task_status("running", "qa_react")
    return {"task_id": task_id}


async def _run_react(state: QaReactState) -> dict[str, Any]:
    agent = _get_react_agent()
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=state["user_message"])]},
        config={"recursion_limit": _REACT_MAX_ITERATIONS * 2 + 4},
    )
    messages = result.get("messages", []) if isinstance(result, dict) else []

    tools_used: list[str] = []
    for m in messages:
        for tc in getattr(m, "tool_calls", None) or []:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name:
                tools_used.append(name)
                observe_tool_call(tool=name, status="ok", latency_ms=None)

    final_text = ""
    if messages:
        last = messages[-1]
        final_text = (getattr(last, "content", "") or "").strip()

    success = bool(final_text)
    report = SubAgentReport(
        skill="qa_react",
        summary=final_text or "未能产出答案。",
        citations=[],
        success=success,
    )

    task_id = state.get("task_id", "")
    if task_id:
        repo = get_task_repo()
        status = "succeeded" if success else "failed"
        await repo.update_task_status(task_id, status)
        inc_task_status(status, "qa_react")

    logger.info(
        "qa_react: iterations=%d tools_used=%s success=%s",
        len(tools_used), tools_used, success,
    )
    return {
        "sub_report": report,
        "react_tools_used": tools_used,
        "react_iterations": len(tools_used),
    }


def build_qa_react_graph():
    g = StateGraph(QaReactState)
    g.add_node("prepare", _prepare)
    g.add_node("react", _run_react)

    g.add_edge(START, "prepare")
    g.add_edge("prepare", "react")
    g.add_edge("react", END)
    return g.compile()
