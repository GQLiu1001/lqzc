"""客服子图 (SubAgent) — M2 重构。

流程: retrieve → plan → approval_check → execute → reflect

三级审批 (approval_check 节点):
  1. 规则兜底: tool ∈ HIGH_RISK_TOOLS → 标记 high
  2. AI 自审: LLM 评估动作安全性, 自动放行 or 维持 high
  3. HITL: 对仍为 high 的动作调 interrupt(), 等待人工决定

interrupt() 暂停图执行, 前端收到 approval_required SSE 事件。
管理员通过 POST /task/{id}/decide 恢复, Command(resume=...) 继续执行。
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agents.customer_service.agent import CUSTOMER_SERVICE_SYSTEM_PROMPT
from app.config import get_settings
from app.memory.task_repo import get_task_repo
from app.models.factory import make_chat
from app.observability.metrics import (
    inc_approval_decision,
    inc_approval_required,
    inc_task_status,
)
from app.schemas.agent_output import SubAgentReport
from app.schemas.approval import ApprovalRecord, PlannedAction
from app.schemas.task import TaskRecord
from app.tools.action_executor import execute_tool
from app.tools.mcp_tools.lqzc_tools import HIGH_RISK_TOOLS
from app.tools.rag_tools.retriever_tool import rag_search
from app.workflows.shared_nodes import safe_dump

logger = logging.getLogger(__name__)

_ORDER_ID_RE = re.compile(r"(?:订单|order[_\s-]*id)[^\d]{0,6}(\d{4,})", re.IGNORECASE)
_FALLBACK_ID_RE = re.compile(r"\b(\d{5,})\b")

_REFUND_RE = re.compile(r"退款|退钱|refund", re.IGNORECASE)
_COUPON_RE = re.compile(r"优惠券|补偿券|补券|coupon", re.IGNORECASE)
_ADDRESS_RE = re.compile(r"改地址|修改地址|换地址|modify.?address", re.IGNORECASE)

AI_REVIEW_PROMPT = """你是风控审核 Agent。判断以下操作是否可以自动放行。
如果操作合理且风险可控,输出 "AUTO_APPROVE";否则输出 "NEED_HUMAN" 并说明原因。
只输出一行: AUTO_APPROVE 或 NEED_HUMAN: <原因>

用户问题: {user_message}
计划操作: {action_json}
知识库上下文: {rag_context}
"""


class CustomerServiceState(TypedDict, total=False):
    user_message: str
    session_id: str
    task_id: str
    rag_hits: list[dict]
    planned_actions: list[dict]
    approval_result: dict
    action_results: list[dict]
    sub_report: SubAgentReport


def _extract_order_id(text: str) -> Optional[str]:
    m = _ORDER_ID_RE.search(text) or _FALLBACK_ID_RE.search(text)
    return m.group(1) if m else None


# ── retrieve ────────────────────────────────────────────────

async def _retrieve(state: CustomerServiceState) -> dict[str, Any]:
    q = state["user_message"]
    hits = await rag_search.ainvoke({"query": q})
    logger.info("cs.retrieve: got %d hits", len(hits))
    return {"rag_hits": hits}


# ── plan ────────────────────────────────────────────────────

async def _plan(state: CustomerServiceState) -> dict[str, Any]:
    text = state["user_message"]
    oid = _extract_order_id(text)
    actions: list[dict] = []

    if oid:
        actions.append(PlannedAction(tool="order_query", args={"order_id": oid}, risk_level="low").model_dump())

    if _REFUND_RE.search(text) and oid:
        actions.append(PlannedAction(
            tool="refund_order",
            args={"order_id": oid, "amount": 0, "reason": "用户主动申请"},
            risk_level="high",
            risk_reason="退款操作不可逆, 涉及资金变动",
        ).model_dump())

    if _COUPON_RE.search(text):
        user_id = state.get("session_id", "unknown")
        actions.append(PlannedAction(
            tool="issue_coupon",
            args={"user_id": user_id, "amount": 10, "reason": "客诉补偿"},
            risk_level="high",
            risk_reason="涉及优惠券发放, 有薅羊毛风险",
        ).model_dump())

    if _ADDRESS_RE.search(text) and oid:
        actions.append(PlannedAction(
            tool="modify_address",
            args={"order_id": oid, "new_address": "待用户提供"},
            risk_level="high",
            risk_reason="修改地址影响物流, 已发货订单不可逆",
        ).model_dump())

    task_id = state.get("task_id") or uuid.uuid4().hex[:16]
    repo = get_task_repo()
    await repo.create_task(TaskRecord(
        task_id=task_id,
        session_id=state.get("session_id", ""),
        skill="customer_service",
        status="running",
    ))
    inc_task_status("running", "customer_service")

    logger.info("cs.plan: %d actions, task_id=%s", len(actions), task_id)
    return {"planned_actions": actions, "task_id": task_id}


# ── approval_check (三级审批) ───────────────────────────────

async def _approval_check(state: CustomerServiceState) -> dict[str, Any]:
    actions = state.get("planned_actions", [])
    high_risk = [a for a in actions if a.get("risk_level") == "high"]

    if not high_risk:
        return {"approval_result": {"approved": True, "method": "auto", "reason": "no high-risk actions"}}

    s = get_settings()
    if not s.enable_approval:
        return {"approval_result": {"approved": True, "method": "disabled", "reason": "approval disabled in config"}}

    # ── Layer 2: AI 自审 ──
    chat = make_chat(temperature=0.0)
    rag_ctx = safe_dump(state.get("rag_hits", []), limit=800)
    action_json = safe_dump(high_risk, limit=500)
    prompt = AI_REVIEW_PROMPT.format(
        user_message=state["user_message"],
        action_json=action_json,
        rag_context=rag_ctx,
    )
    try:
        resp = await chat.ainvoke([SystemMessage(content=prompt)])
        ai_opinion = (resp.content or "").strip() if hasattr(resp, "content") else str(resp)
    except Exception as exc:
        logger.warning("cs.approval_check: AI review failed: %s", exc)
        ai_opinion = "NEED_HUMAN: AI 审核异常"

    logger.info("cs.approval_check: AI opinion=%s", ai_opinion[:100])

    if ai_opinion.startswith("AUTO_APPROVE"):
        return {"approval_result": {"approved": True, "method": "ai_review", "reason": ai_opinion}}

    # ── Layer 3: HITL interrupt ──
    task_id = state.get("task_id", "")
    session_id = state.get("session_id", "")
    repo = get_task_repo()

    await repo.update_task_status(task_id, "waiting_approval")
    inc_task_status("waiting_approval", "customer_service")
    await repo.create_approval(ApprovalRecord(
        task_id=task_id,
        session_id=session_id,
        tool=high_risk[0]["tool"],
        args=high_risk[0].get("args", {}),
        risk_level="high",
        risk_reason=high_risk[0].get("risk_reason", ""),
        ai_review=ai_opinion,
    ))
    inc_approval_required()

    decision = interrupt({
        "type": "approval_required",
        "task_id": task_id,
        "session_id": session_id,
        "actions": high_risk,
        "ai_review": ai_opinion,
    })

    approved = decision.get("approved", False) if isinstance(decision, dict) else bool(decision)
    decided_by = decision.get("decided_by", "human") if isinstance(decision, dict) else "human"
    inc_approval_decision(approved)

    await repo.decide_approval(task_id, approved, decided_by)
    if approved:
        await repo.update_task_status(task_id, "running")
        inc_task_status("running", "customer_service")
    else:
        await repo.update_task_status(task_id, "failed", error="审批被拒绝")
        inc_task_status("failed", "customer_service")

    return {"approval_result": {"approved": approved, "method": "human", "decided_by": decided_by}}


def _route_after_approval(state: CustomerServiceState) -> str:
    result = state.get("approval_result", {})
    if result.get("approved", False):
        return "execute"
    return "reflect"


# ── execute ─────────────────────────────────────────────────

async def _execute(state: CustomerServiceState) -> dict[str, Any]:
    task_id = state.get("task_id", "")
    actions = state.get("planned_actions", [])
    results: list[dict] = []

    for action in actions:
        tool_name = action["tool"]
        args = action.get("args", {})

        approved = state.get("approval_result", {}).get("approved", False)
        if action.get("risk_level") == "high" and not approved:
            results.append({"tool": tool_name, "status": "rejected", "result": None})
            continue

        record = await execute_tool(task_id, tool_name, args)
        results.append(record.model_dump())

    repo = get_task_repo()
    all_ok = all(r.get("status") == "ok" for r in results)
    final_status = "succeeded" if all_ok else "failed"
    await repo.update_task_status(task_id, final_status)
    inc_task_status(final_status, "customer_service")

    logger.info("cs.execute: %d actions, all_ok=%s", len(results), all_ok)
    return {"action_results": results}


# ── reflect ─────────────────────────────────────────────────

async def _reflect(state: CustomerServiceState) -> dict[str, Any]:
    approval = state.get("approval_result", {})
    if not approval.get("approved", True) and approval.get("method") == "human":
        report = SubAgentReport(
            skill="customer_service",
            summary="该操作已被管理员拒绝, 如有疑问请联系人工客服。",
            success=False,
        )
        return {"sub_report": report}

    chat = make_chat(temperature=0.1)
    hits = state.get("rag_hits") or []
    action_results = state.get("action_results") or []

    context = {
        "knowledge": hits,
        "action_results": action_results,
    }
    user = (
        f"用户问题:{state['user_message']}\n\n"
        f"可用上下文 (JSON):\n{safe_dump(context, limit=2000)}\n\n"
        "请给出: summary (中文,<=120字,引用关键信息), 与一个布尔 success。"
    )
    resp = await chat.ainvoke(
        [SystemMessage(content=CUSTOMER_SERVICE_SYSTEM_PROMPT), HumanMessage(content=user)]
    )
    summary = (resp.content or "").strip() if hasattr(resp, "content") else str(resp)
    citations = [h["doc_id"] for h in hits[:3]]
    report = SubAgentReport(
        skill="customer_service", summary=summary, citations=citations, success=True
    )
    return {"sub_report": report}


# ── 构建子图 ────────────────────────────────────────────────

def build_customer_service_graph():
    g = StateGraph(CustomerServiceState)
    g.add_node("retrieve", _retrieve)
    g.add_node("plan", _plan)
    g.add_node("approval_check", _approval_check)
    g.add_node("execute", _execute)
    g.add_node("reflect", _reflect)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "plan")
    g.add_edge("plan", "approval_check")
    g.add_conditional_edges(
        "approval_check",
        _route_after_approval,
        {"execute": "execute", "reflect": "reflect"},
    )
    g.add_edge("execute", "reflect")
    g.add_edge("reflect", END)

    return g.compile()
