"""WarehouseAgent — 仓储域领域执行器.

已被 Supervisor 判定为 warehouse 域后，WarehouseAgent 负责：
1. 构造仓储域运行时权限约束
2. 内部通过两个 subagent 隔离低风险查询和高风险执行
3. 调用 Deep Agent 进行 Skill 匹配 + subagent 委派 + 工具调用
4. 归一化结果为 DomainAgentResult 返回给 Supervisor

subagent 划分：
  - inventory_subagent: 库存查询（低风险，无审批）
  - approval_subagent:  出库审批（高风险，interrupt_on）
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.warehouse_agent.approval_subagent import build_approval_subagent
from app.agents.warehouse_agent.inventory_subagent import build_inventory_subagent
from app.schemas.agent import DomainAgentResult

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parents[3] / "skills"

WAREHOUSE_SYSTEM_PROMPT = """\
你是仓储域智能助理，只处理仓储相关问题。
你必须遵守以下规则：

1. 只处理仓储域问题：库存、库位、出库、波次、审批、盘点、仓储规则等。
2. 不处理商城域问题：订单详情、商品咨询、退款售后、物流签收等。
3. 涉及库存、出库申请、审批流等问题时，必须以当前 user_context 的权限范围为准。
4. 高风险仓储操作必须通过审批机制，不得绕过 interrupt。
5. 优先复用已命中的 Skill 指引，再决定是否调用工具。
6. 如果问题不属于仓储域，明确降级，不要编造答案。

你有两个专业子代理可以委派任务：
- warehouse_inventory_subagent: 处理库存查询、库存流水、库存异常分析
- warehouse_approval_subagent: 处理出库申请、审批状态查询（高风险操作会触发审批中断）

根据问题类型选择合适的子代理，不要自己直接调用底层工具。"""


class WarehouseAgent:

    def __init__(self, model: BaseChatModel, checkpointer: BaseCheckpointSaver):
        self._model = model
        self._checkpointer = checkpointer

        inventory_sub = build_inventory_subagent()
        approval_sub = build_approval_subagent()

        self._agent = create_deep_agent(
            model=model,
            system_prompt=WAREHOUSE_SYSTEM_PROMPT,
            subagents=[inventory_sub, approval_sub],
            skills=[
                "/skills/shared/response_format/",
            ],
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir=str(_SKILLS_ROOT.parent)),
            name="warehouse_agent",
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
                        "checkpoint_ns": "warehouse",
                    },
                },
            )
        except Exception:
            logger.exception("WarehouseAgent invoke failed for session %s", session_id)
            return DomainAgentResult(
                route="warehouse",
                answer="抱歉，仓储域处理异常，请稍后再试。",
                status="error",
                error_code="WAREHOUSE_AGENT_ERROR",
                error_message="WarehouseAgent 内部执行异常",
            )

        return self._normalize_result(result)

    # ── private helpers ───────────────────────────────────────────────

    @staticmethod
    def _build_runtime_guard(user_context: dict) -> str:
        return f"""\
当前请求上下文：
- domain=warehouse
- userType={user_context.get("user_type")}
- userId={user_context.get("user_id")}
- role={user_context.get("role")}
- warehouseScope={user_context.get("warehouse_scope", [])}

执行约束：
1. 仅处理仓储域问题；
2. 只允许在当前角色权限范围内查询库存、出库、审批数据；
3. 高风险操作必须通过审批，不得跳过；
4. 查询失败时说明原因，不要编造结果。"""

    @staticmethod
    def _normalize_result(result: dict) -> DomainAgentResult:
        answer = ""
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            answer = last.content if hasattr(last, "content") else str(last)

        # Check for interrupt (approval flow triggered)
        interrupt = result.get("__interrupt__") or result.get("interrupt")
        if interrupt:
            return DomainAgentResult(
                route="warehouse",
                answer="该操作涉及仓储审批，当前已进入待审批状态。",
                tool_calls=WarehouseAgent._extract_tool_calls(result),
                skill_used=WarehouseAgent._extract_skills(result),
                status="need_approval",
                interrupt=interrupt if isinstance(interrupt, dict) else {"raw": str(interrupt)},
            )

        tool_calls = WarehouseAgent._extract_tool_calls(result)
        skill_used = WarehouseAgent._extract_skills(result)

        return DomainAgentResult(
            route="warehouse",
            answer=answer or "抱歉，当前仓储问题暂时无法处理，请稍后再试。",
            tool_calls=tool_calls,
            skill_used=skill_used,
            status="success" if answer else "fallback",
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
                for tag in ("inventory_query", "outbound_approval", "response_format"):
                    if tag in content and tag not in skills:
                        skills.append(tag)
        return skills
