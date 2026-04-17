"""MallAgent — 商城域领域执行器.

已被 Supervisor 判定为 mall 域后，MallAgent 负责：
1. 构造商城域运行时权限约束
2. 调用 Deep Agent 进行 Skill 匹配 + 工具调用
3. 归一化结果为 DomainAgentResult 返回给 Supervisor
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.messages import HumanMessage, SystemMessage

from app.schemas.agent import DomainAgentResult
from app.tools.rag_tools import shared_policy_rag_search
from app.tools.mall_tools import (
    aftersale_policy_query,
    get_top_sales,
    logistics_trace_query,
    mall_rag_search,
    my_order_query,
    order_detail_query,
    product_consult_query,
    search_inventory,
)

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"

MALL_SYSTEM_PROMPT = """\
你是商城域智能助理，只处理商城相关问题。
你必须遵守以下规则：

1. 只处理商城域问题：订单、商品、售后、退款、物流、配送、发票等。
2. 不处理仓库域问题：库存、波次、出库审批、仓内作业、盘点等。
3. 涉及用户订单、售后、地址、手机号等敏感信息时，必须以当前 user_context 的身份范围为准。
4. 如果当前问题无法在商城域内解决，返回明确的降级说明，不要编造。
5. 优先复用已命中的 Skill 指引，再决定是否调用工具。
6. 回答面向终端用户时保持简洁、明确、可执行。
"""

_MALL_TOOLS = [
    my_order_query,
    order_detail_query,
    product_consult_query,
    aftersale_policy_query,
    logistics_trace_query,
    mall_rag_search,
    shared_policy_rag_search,
    get_top_sales,
    search_inventory,
]

_MALL_SKILLS = [
    "/skills/shared/response_format/",
    "/skills/mall/order_query/",
    "/skills/mall/product_consult/",
]


class MallAgent:

    def __init__(self, model: BaseChatModel, checkpointer: BaseCheckpointSaver):
        self._model = model
        self._checkpointer = checkpointer
        self._agent = create_deep_agent(
            model=model,
            tools=_MALL_TOOLS,
            system_prompt=MALL_SYSTEM_PROMPT,
            skills=_MALL_SKILLS,
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir=str(_SKILLS_ROOT.parent)),
            name="mall_agent",
        )

    async def invoke(
        self,
        session_id: str,
        message: str,
        user_context: dict,
    ) -> DomainAgentResult:
        runtime_guard = self._build_runtime_guard(user_context)

        try:
            result = await self._agent.ainvoke(
                {
                    "messages": [
                        SystemMessage(content=runtime_guard),
                        HumanMessage(content=message),
                    ],
                },
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_ns": "mall",
                    },
                },
            )
        except Exception:
            logger.exception("MallAgent invoke failed for session %s", session_id)
            return DomainAgentResult(
                route="mall",
                answer="抱歉，商城域处理异常，请稍后再试。",
                status="error",
                error_code="MALL_AGENT_ERROR",
                error_message="MallAgent 内部执行异常",
            )

        return self._normalize_result(result)

    # ── private helpers ───────────────────────────────────────────────

    @staticmethod
    def _build_runtime_guard(user_context: dict) -> str:
        return f"""\
当前请求上下文：
- domain=mall
- userType={user_context.get("user_type")}
- userId={user_context.get("user_id")}
- role={user_context.get("role")}

执行约束：
1. 仅处理商城域问题；
2. 涉及订单/售后/地址等敏感信息时，只能查询当前用户有权限的数据；
3. 不得要求用户再次提供系统已知身份信息；
4. 查询失败时说明原因，不要编造结果。"""

    @staticmethod
    def _normalize_result(result: dict) -> DomainAgentResult:
        answer = ""
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            answer = last.content if hasattr(last, "content") else str(last)

        tool_calls = MallAgent._extract_tool_calls(result)
        skill_used = MallAgent._extract_skills(result)

        return DomainAgentResult(
            route="mall",
            answer=answer or "抱歉，当前商城问题暂时无法处理，请稍后再试。",
            tool_calls=tool_calls,
            skill_used=skill_used,
            status="success" if answer else "fallback",
            raw=None,
        )

    @staticmethod
    def _extract_tool_calls(result: dict) -> list[str]:
        names: list[str] = []
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    if name and name not in names:
                        names.append(name)
        return names

    @staticmethod
    def _extract_skills(result: dict) -> list[str]:
        skills: list[str] = []
        for msg in result.get("messages", []):
            content = msg.content if hasattr(msg, "content") else ""
            if isinstance(content, str):
                for tag in ("order_query", "product_consult", "response_format"):
                    if tag in content and tag not in skills:
                        skills.append(tag)
        return skills
