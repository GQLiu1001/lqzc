"""提供与注册表相关的实现。"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from app.skills.base import BaseSkill, SkillMatch, SkillSelection, SkillDomain
from app.skills.customer import (
    AfterSaleIntakeSkill,
    CustomerReplyDraftSkill,
    OrderStatusExplainSkill,
    RefundPolicySkill,
)
from app.skills.warehouse import (
    InventoryExceptionSkill,
    ReplenishmentSuggestionSkill,
    StockHoldReleaseSkill,
    WarehouseSopRetrievalSkill,
)


def _default_skills() -> list[BaseSkill]:
    """返回系统默认加载的 skill 列表。

    这里决定了“系统一启动就有哪些技能可用”。
    以后如果增加新技能，通常会在这里注册进去。
    """
    return [
        RefundPolicySkill(),
        StockHoldReleaseSkill(),
        OrderStatusExplainSkill(),
        InventoryExceptionSkill(),
        ReplenishmentSuggestionSkill(),
        AfterSaleIntakeSkill(),
        CustomerReplyDraftSkill(),
        WarehouseSopRetrievalSkill(),
    ]


class SkillRegistry:
    """技能注册表。

    你可以把它理解成“所有 skill 的总名单 + 查询中心 + 规则路由器”。
    它负责：
    - 存放全部 skill
    - 按名字查 skill
    - 把 skill 列表整理成模型可读目录
    - 用规则从多个 skill 中选一个最合适的
    """
    def __init__(self, skills: list[BaseSkill] | None = None) -> None:
        """加载技能，并建立名称索引。

        这里会先按优先级排序，再缓存一份按名称访问的字典，
        方便后面既能遍历，也能快速按名字取。
        """
        loaded = skills or _default_skills()
        self._skills = tuple(sorted(loaded, key=lambda item: (item.definition.priority, item.definition.name)))
        self._by_name = {item.definition.name: item for item in self._skills}

    def names(self) -> list[str]:
        """返回当前可用对象的名称列表，方便上层展示或遍历。"""
        return [item.definition.name for item in self._skills]

    def catalog_lines(self) -> list[str]:
        """把技能定义整理成可读文本行。

        这个输出主要是给 LLM 路由器看的，让模型知道：
        - skill 名字
        - 属于哪个 domain
        - 风险等级
        - 是否需要审批
        - 大致描述
        """
        lines: list[str] = []
        for item in self._skills:
            definition = item.definition
            lines.append(
                f"{definition.name} | domain={definition.domain} | risk={definition.risk_level} | "
                f"approval={definition.requires_approval} | {definition.description}"
            )
        return lines

    def get(self, name: str) -> BaseSkill | None:
        """按给定标识获取对应对象，找不到时返回空值。"""
        return self._by_name.get(name)

    def select_rule_based(self, *, message: str, context: Mapping[str, Any] | None = None) -> SkillSelection:
        """基于规则从全部技能中选一个最合适的。

        这里的流程建议你重点理解：
        1. 先推断一个大致 domain 提示
        2. 再让每个 skill 自己打分
        3. 根据 domain 提示对分数做加减权
        4. 从候选里选出得分最高者
        5. 如果都不理想，则回退到某个默认 skill
        """
        context_map = context or {}
        domain_hint = self._infer_domain_hint(message=message, context=context_map)

        candidates: list[tuple[int, int, str, BaseSkill, SkillMatch]] = []
        for skill in self._skills:
            # 每个 skill 自己判断“这条消息像不像我负责处理的类型”。
            match = skill.evaluate(message=message, context=context_map)
            adjusted_score = match.score

            if domain_hint is not None:
                # 如果整体像仓储问题，就给仓储类 skill 额外加分。
                if skill.definition.domain == domain_hint:
                    adjusted_score += 4
                else:
                    adjusted_score -= 2

            if adjusted_score <= 0 and not skill.definition.default_skill_for_domain:
                continue

            adjusted_match = replace(
                match,
                score=max(1, adjusted_score),
                reason=f"{match.reason}; domain_hint={domain_hint or 'none'}; adjusted={max(1, adjusted_score)}",
            )
            candidates.append(
                (adjusted_match.score, -skill.definition.priority, skill.definition.name, skill, adjusted_match)
            )

        if candidates:
            chosen = max(candidates, key=lambda item: (item[0], item[1], item[2]))
            _, _, _, skill, match = chosen
            return SkillSelection(definition=skill.definition, match=match, route_source="rule")

        fallback = self._fallback_for_domain(domain_hint)
        fallback_match = SkillMatch(
            skill_name=fallback.definition.name,
            score=1,
            reason=f"fallback for domain={domain_hint or 'customer_service'}",
            signals=("fallback",),
        )
        return SkillSelection(definition=fallback.definition, match=fallback_match, route_source="rule")

    def selection_from_name(
        self,
        *,
        skill_name: str,
        route_source: str,
        route_confidence: float | None,
        reason: str,
    ) -> SkillSelection | None:
        """把一个 skill_name 重新包装成完整的 `SkillSelection`。

        这个方法主要给 LLM 路由器使用：
        模型只会返回 skill 名字，但工作流真正需要的是完整 skill 定义。
        """
        skill = self.get(skill_name)
        if skill is None:
            return None
        match = SkillMatch(
            skill_name=skill.definition.name,
            score=100,
            reason=reason,
            signals=("llm",),
        )
        return SkillSelection(
            definition=skill.definition,
            match=match,
            route_source="llm" if route_source == "llm" else "rule",
            route_confidence=route_confidence,
        )

    def _fallback_for_domain(self, domain_hint: SkillDomain | None) -> BaseSkill:
        """当规则匹配都很弱时，按业务域返回一个保底技能。"""
        if domain_hint == "warehouse":
            return self._by_name["inventory_exception_skill"]
        return self._by_name["order_status_explain_skill"]

    @staticmethod
    def _infer_domain_hint(*, message: str, context: Mapping[str, Any]) -> SkillDomain | None:
        """先粗粒度判断这条消息更像客服域还是仓储域。

        这一步不是最终结论，而是给后面的具体 skill 评分提供一个偏置提示。
        """
        channel = str(context.get("channel") or "").lower()
        if "warehouse" in channel:
            return "warehouse"
        if any(token in channel for token in ("customer", "service", "support")):
            return "customer_service"

        lowered = message.lower()
        warehouse_tokens = ("库存", "仓库", "仓储", "补货", "sop", "拣货", "入库", "出库", "锁库", "冻结", "释放")
        customer_tokens = ("订单", "物流", "售后", "退款", "补偿", "工单", "客服", "回复")

        warehouse_hit = sum(1 for token in warehouse_tokens if token in lowered)
        customer_hit = sum(1 for token in customer_tokens if token in lowered)

        if warehouse_hit > customer_hit:
            return "warehouse"
        return "customer_service"
