from __future__ import annotations

import logging
import re

from langchain_ollama import ChatOllama

from app.core.config import settings
from app.supervisor.state import SupervisorState

logger = logging.getLogger(__name__)

# ── 第一层：身份直接限流 ──────────────────────────────────────────────
_CUSTOMER_ONLY_ROUTE = "mall"
_WAREHOUSE_ROLES = {"admin", "staff", "warehouse_manager"}

# ── 第二层：关键词意图分类 ─────────────────────────────────────────────
_MALL_KEYWORDS = [
    "订单", "商品", "退款", "配送", "售后", "发票", "物流",
    "签收", "下单", "购买", "收货", "退换", "快递", "热销",
    "优惠", "券", "积分", "会员", "价格", "型号",
]
_WAREHOUSE_KEYWORDS = [
    "库存", "入库", "出库", "波次", "盘点", "审批",
    "仓库", "仓储", "调拨", "库位", "冲正",
]

_MALL_PATTERN = re.compile("|".join(_MALL_KEYWORDS))
_WAREHOUSE_PATTERN = re.compile("|".join(_WAREHOUSE_KEYWORDS))


def _keyword_route(message: str) -> tuple[str | None, str]:
    mall_hits = len(_MALL_PATTERN.findall(message))
    wh_hits = len(_WAREHOUSE_PATTERN.findall(message))
    if mall_hits > 0 and wh_hits == 0:
        return "mall", "关键词命中商城域"
    if wh_hits > 0 and mall_hits == 0:
        return "warehouse", "关键词命中仓储域"
    if mall_hits > 0 and wh_hits > 0:
        return None, "关键词同时命中商城和仓储域，需要 LLM 补充判断"
    return None, "未命中关键词"


# ── 第三层：LLM 意图分类器 ─────────────────────────────────────────────
_CLASSIFIER_PROMPT = """\
你是一个意图路由分类器。根据用户的问题，判断它属于哪个业务域。

只能输出以下三个值之一（不要输出任何其他内容）：
- mall（商城域：订单、商品、退款、售后、物流、配送、发票等）
- warehouse（仓储域：库存、出库、入库、审批、盘点、调拨、仓库等）
- fallback（无法判断）

用户问题：{message}
"""


async def _llm_route(message: str) -> tuple[str, str, float]:
    try:
        llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
        resp = await llm.ainvoke(_CLASSIFIER_PROMPT.format(message=message))
        raw = resp.content.strip().lower()
        if "mall" in raw:
            return "mall", "LLM 分类为商城域", 0.8
        if "warehouse" in raw:
            return "warehouse", "LLM 分类为仓储域", 0.8
    except Exception:
        logger.warning("LLM router failed, falling back", exc_info=True)
    return "fallback", "LLM 无法判断或调用失败", 0.0


# ── 节点实现 ──────────────────────────────────────────────────────────

async def route_node(state: SupervisorState) -> dict:
    """根据身份 + 关键词 + LLM 判断业务域。"""
    user_ctx = state["user_context"]
    message = state["message"]
    user_type = user_ctx.get("user_type", "customer")
    role = user_ctx.get("role", "")

    # 第一层：customer 只能走 mall
    if user_type == "customer":
        return {
            "route": _CUSTOMER_ONLY_ROUTE,
            "route_reason": "customer 身份默认走商城域",
            "intent": "auto",
            "domain": "mall",
        }

    # 第二层：关键词路由
    kw_route, kw_reason = _keyword_route(message)
    if kw_route is not None:
        if kw_route == "warehouse" and role not in _WAREHOUSE_ROLES:
            return {
                "route": "fallback",
                "route_reason": f"关键词命中仓储域但角色 {role} 无权限",
                "intent": "auto",
                "domain": "warehouse",
                "status": "forbidden",
                "error": "WAREHOUSE_ROLE_DENIED",
            }
        return {
            "route": kw_route,
            "route_reason": kw_reason,
            "intent": "auto",
            "domain": kw_route,
        }

    # 第三层：LLM 分类
    llm_route, llm_reason, confidence = await _llm_route(message)
    if llm_route == "warehouse" and role not in _WAREHOUSE_ROLES:
        return {
            "route": "fallback",
            "route_reason": f"LLM 分类为仓储域但角色 {role} 无权限",
            "intent": "auto",
            "domain": "warehouse",
            "status": "forbidden",
            "error": "WAREHOUSE_ROLE_DENIED",
        }
    if confidence < 0.5:
        llm_route = "fallback"

    return {
        "route": llm_route,
        "route_reason": llm_reason,
        "intent": "auto",
        "domain": llm_route if llm_route != "fallback" else "",
    }


def route_dispatcher(state: SupervisorState) -> str:
    """条件边：根据 route 字段分发到对应节点。"""
    return state.get("route", "fallback")


async def fallback_node(state: SupervisorState) -> dict:
    """兜底节点：身份无权限、意图不清晰、Agent 执行失败等。"""
    error = state.get("error")
    if error == "WAREHOUSE_ROLE_DENIED":
        return {
            "route": "fallback",
            "status": "forbidden",
            "answer": "当前角色无权执行仓库相关操作。",
            "tool_calls": [],
        }
    return {
        "route": "fallback",
        "status": "fallback",
        "answer": "当前问题暂时无法明确归类到商城或仓库场景，请补充订单号、商品信息或仓库信息后再试。",
        "tool_calls": [],
    }


async def finalize_node(state: SupervisorState) -> dict:
    """统一收敛输出字段。"""
    answer = state.get("answer") or "抱歉，当前问题暂时无法处理，请稍后重试。"
    return {
        "session_id": state["session_id"],
        "route": state.get("route", "fallback"),
        "answer": answer,
        "tool_calls": state.get("tool_calls", []),
        "status": state.get("status", "success"),
        "interrupt": state.get("interrupt"),
    }
