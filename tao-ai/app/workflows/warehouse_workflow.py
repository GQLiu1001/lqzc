"""仓储子图 (SubAgent) — M5 第一阶段。

流程: retrieve → plan → execute → reflect

定位:
  - 先支持查询类场景,不涉及审批和写操作
  - 典型问题: 出库量、库存快照、物流进度
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.warehouse.agent import WAREHOUSE_SYSTEM_PROMPT
from app.memory.task_repo import get_task_repo
from app.models.factory import make_chat
from app.observability.metrics import inc_task_status
from app.schemas.agent_output import SubAgentReport
from app.schemas.approval import PlannedAction
from app.schemas.task import TaskRecord
from app.tools.action_executor import execute_tool
from app.workflows.shared_nodes import safe_dump

logger = logging.getLogger(__name__)

_WAREHOUSE_RE = re.compile(r"([A-Za-z])仓")
_SKU_RE = re.compile(r"(SKU[-_ ]?\d+)", re.IGNORECASE)
_ORDER_ID_RE = re.compile(r"(?:订单|order[_\\s-]*id)[^\\d]{0,6}(\\d{4,})", re.IGNORECASE)

_STOCK_KEYWORDS = re.compile(r"库存|现存|可用库存|stock", re.IGNORECASE)
_LOGISTICS_KEYWORDS = re.compile(r"物流|运单|在途|配送|track", re.IGNORECASE)


class WarehouseState(TypedDict, total=False):
    user_message: str
    session_id: str
    task_id: str
    rag_hits: list[dict]
    planned_actions: list[dict]
    action_results: list[dict]
    sub_report: SubAgentReport


def _extract_warehouse(text: str) -> str:
    m = _WAREHOUSE_RE.search(text)
    if not m:
        return "A"
    return m.group(1).upper()


def _extract_sku(text: str) -> str:
    m = _SKU_RE.search(text)
    if not m:
        return "SKU-9527"
    sku = m.group(1).upper().replace(" ", "").replace("_", "-")
    return sku


def _extract_order_id(text: str) -> Optional[str]:
    m = _ORDER_ID_RE.search(text)
    return m.group(1) if m else None


async def _retrieve(state: WarehouseState) -> dict[str, Any]:
    from app.tools.rag_tools.retriever_tool import rag_search

    q = state["user_message"]
    hits = await rag_search.ainvoke({"query": q, "source": "warehouse_sop"})
    logger.info("warehouse.retrieve: got %d hits", len(hits))
    return {"rag_hits": hits}


async def _plan(state: WarehouseState) -> dict[str, Any]:
    text = state["user_message"]
    warehouse = _extract_warehouse(text)
    sku = _extract_sku(text)
    order_id = _extract_order_id(text)

    actions: list[dict] = [
        PlannedAction(
            tool="inventory_metric",
            args={"warehouse": warehouse, "sku": sku},
            risk_level="low",
        ).model_dump()
    ]

    if _STOCK_KEYWORDS.search(text):
        actions.append(
            PlannedAction(
                tool="inventory_stock_query",
                args={"warehouse": warehouse, "sku": sku},
                risk_level="low",
            ).model_dump()
        )

    if _LOGISTICS_KEYWORDS.search(text) and order_id:
        actions.append(
            PlannedAction(
                tool="logistics_query",
                args={"order_id": order_id},
                risk_level="low",
            ).model_dump()
        )

    task_id = state.get("task_id") or uuid.uuid4().hex[:16]
    repo = get_task_repo()
    await repo.create_task(
        TaskRecord(
            task_id=task_id,
            session_id=state.get("session_id", ""),
            skill="warehouse",
            status="running",
        )
    )
    inc_task_status("running", "warehouse")

    logger.info("warehouse.plan: %d actions, task_id=%s", len(actions), task_id)
    return {"planned_actions": actions, "task_id": task_id}


async def _execute(state: WarehouseState) -> dict[str, Any]:
    task_id = state.get("task_id", "")
    actions = state.get("planned_actions", [])
    results: list[dict] = []

    for action in actions:
        tool_name = action["tool"]
        args = action.get("args", {})
        record = await execute_tool(task_id, tool_name, args)
        results.append(record.model_dump())

    repo = get_task_repo()
    all_ok = all(r.get("status") == "ok" for r in results)
    final_status = "succeeded" if all_ok else "failed"
    await repo.update_task_status(task_id, final_status)
    inc_task_status(final_status, "warehouse")

    logger.info("warehouse.execute: %d actions, all_ok=%s", len(results), all_ok)
    return {"action_results": results}


async def _reflect(state: WarehouseState) -> dict[str, Any]:
    chat = make_chat(temperature=0.1)
    hits = state.get("rag_hits") or []
    action_results = state.get("action_results") or []

    context = {
        "knowledge": hits,
        "action_results": action_results,
    }
    user = (
        f"用户问题:{state['user_message']}\\n\\n"
        f"可用上下文 (JSON):\\n{safe_dump(context, limit=2000)}\\n\\n"
        "请输出简洁结论(中文 <=120字)与是否成功。"
    )
    resp = await chat.ainvoke(
        [SystemMessage(content=WAREHOUSE_SYSTEM_PROMPT), HumanMessage(content=user)]
    )
    summary = (resp.content or "").strip() if hasattr(resp, "content") else str(resp)
    citations = [h["doc_id"] for h in hits[:3]]
    report = SubAgentReport(skill="warehouse", summary=summary, citations=citations, success=True)
    return {"sub_report": report}


def build_warehouse_graph():
    g = StateGraph(WarehouseState)
    g.add_node("retrieve", _retrieve)
    g.add_node("plan", _plan)
    g.add_node("execute", _execute)
    g.add_node("reflect", _reflect)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "plan")
    g.add_edge("plan", "execute")
    g.add_edge("execute", "reflect")
    g.add_edge("reflect", END)
    return g.compile()

