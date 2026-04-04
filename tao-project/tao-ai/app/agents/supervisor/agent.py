"""提供与Agent相关的实现。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import Any, Mapping

from app.config import settings
from app.models.chat import ChatService
from app.skills.registry import SkillRegistry


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RouteDecision:
    """路由决策结果。

    SupervisorAgent 不是直接回答用户，而是先输出一份“派单结果”：
    应该去哪个 agent、走哪个技能、是否有风险、需要哪些工具。
    """
    agent: str
    skill: str
    risk_level: str
    requires_approval: bool
    retrieval_domain: str
    tool_hints: tuple[str, ...]
    system_instruction: str
    response_contract: str
    route_reason: str
    route_source: str
    route_confidence: float | None = None


class SupervisorAgent:
    """总控 Agent，专门负责路由，不直接负责业务回答。

    这里的核心职责是：
    - 识别用户问题属于哪个业务域
    - 为问题挑选最合适的 skill
    - 在规则不足时，用 LLM 做兜底判断
    """
    def __init__(self, *, skill_registry: SkillRegistry | None = None, chat_service: ChatService | None = None) -> None:
        """初始化总控Agent，把运行时依赖和基础状态准备好。"""
        self.skill_registry = skill_registry or SkillRegistry()
        self.chat_service = chat_service

    async def route(self, message: str, *, context: Mapping[str, Any] | None = None) -> RouteDecision:
        """综合规则路由和 LLM 路由，给出最终派单结果。

        这里采用“规则优先，LLM 兜底”的设计：
        - 规则命中强时，稳定、可解释、成本低。
        - 规则分数太低时，再让大模型从技能清单里选一个。
        """
        context_map = context or {}
        # 先走规则路由。这里主要看关键词、正则信号、上下文加分等。
        rule_selection = self.skill_registry.select_rule_based(message=message, context=context_map)
        final_selection = rule_selection

        # 只有在规则分数偏低时，才启用 LLM 做二次判断，避免每次都多走一轮模型。
        should_use_llm_router = (
            settings.enable_llm_skill_router
            and self.chat_service is not None
            and rule_selection.match.score < settings.llm_skill_router_min_rule_score
        )
        logger.info(
            "skill.route.rule score=%s skill=%s threshold=%s llm_candidate=%s",
            rule_selection.match.score,
            rule_selection.definition.name,
            settings.llm_skill_router_min_rule_score,
            should_use_llm_router,
        )
        if should_use_llm_router:
            llm_skill_name, confidence, reason = await self._route_with_llm(message=message, context=context_map)
            if llm_skill_name:
                # 把 LLM 产出的 skill_name 再映射回系统内部定义的 SkillSelection。
                llm_selection = self.skill_registry.selection_from_name(
                    skill_name=llm_skill_name,
                    route_source="llm",
                    route_confidence=confidence,
                    reason=reason,
                )
                if llm_selection is not None:
                    logger.info(
                        "skill.route.llm selected_skill=%s confidence=%s reason=%s",
                        llm_selection.definition.name,
                        confidence,
                        reason,
                    )
                    final_selection = llm_selection
            else:
                logger.info("skill.route.llm.fallback reason=%s", reason)

        # 最后把技能定义展开成工作流真正要消费的字段。
        definition = final_selection.definition
        return RouteDecision(
            agent=definition.domain,
            skill=definition.name,
            risk_level=definition.risk_level,
            requires_approval=definition.requires_approval,
            retrieval_domain=definition.retrieval_domain,
            tool_hints=definition.tool_hints,
            system_instruction=definition.system_instruction,
            response_contract=definition.response_contract,
            route_reason=final_selection.match.reason,
            route_source=final_selection.route_source,
            route_confidence=final_selection.route_confidence,
        )

    async def _route_with_llm(self, *, message: str, context: Mapping[str, Any]) -> tuple[str | None, float | None, str]:
        """让大模型在候选技能中选一个最合适的。

        注意这里不是开放问答，而是“受限分类”：
        模型只能从给定技能集合中选，不允许自己发明新 skill。
        这样更容易控输出，也更适合线上系统。
        """
        prompt = (
            "你是技能路由器。你必须从给定技能集合中选择一个 skill。\n"
            "只允许输出 JSON 对象，格式为："
            '{"skill":"<name>","confidence":0.0-1.0,"reason":"<short reason>"}。\n'
            "不要输出 Markdown，不要输出额外文本。"
        )
        # catalog_lines 会把所有技能整理成一组可读描述，供模型做对比判断。
        catalog = "\n".join(f"- {line}" for line in self.skill_registry.catalog_lines())
        context_text = json.dumps(dict(context), ensure_ascii=False)
        user_text = (
            f"用户问题：{message}\n"
            f"上下文：{context_text}\n"
            f"可选技能：\n{catalog}\n"
        )

        try:
            raw = await asyncio.wait_for(
                self.chat_service.generate(
                    system_prompt=prompt,
                    user_message=user_text,
                    context="",
                ),
                timeout=settings.llm_skill_router_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("skill.route.llm.error timeout_or_exception=%s", exc)
            return None, None, f"llm_router_fallback: {exc}"

        # 模型可能吐出 Markdown 代码块或夹杂解释文字，所以这里要做一次容错解析。
        parsed = self._try_parse_router_json(raw)
        if parsed is None:
            return None, None, "llm_router_invalid_json"

        skill_name = str(parsed.get("skill") or "").strip()
        if not skill_name:
            return None, None, "llm_router_empty_skill"

        confidence_value: float | None = None
        try:
            confidence_raw = parsed.get("confidence")
            if confidence_raw is not None:
                confidence_value = max(0.0, min(1.0, float(confidence_raw)))
        except (TypeError, ValueError):
            confidence_value = None

        reason = str(parsed.get("reason") or "llm selected skill")
        return skill_name, confidence_value, reason

    @staticmethod
    def _try_parse_router_json(raw: str) -> dict[str, Any] | None:
        """尽量从模型输出里提取 JSON。

        真实线上里，模型即使被要求“只输出 JSON”，也可能输出：
        - ```json 代码块
        - JSON 前后多几句解释
        - 格式稍微不标准的文本

        所以这里做了两层容错：
        1. 先直接整体解析
        2. 不行就正则截取最像 JSON 的 `{...}` 再解析
        """
        content = raw.strip()
        if not content:
            return None

        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
