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
    def __init__(self, skills: list[BaseSkill] | None = None) -> None:
        loaded = skills or _default_skills()
        self._skills = tuple(sorted(loaded, key=lambda item: (item.definition.priority, item.definition.name)))
        self._by_name = {item.definition.name: item for item in self._skills}

    def names(self) -> list[str]:
        return [item.definition.name for item in self._skills]

    def catalog_lines(self) -> list[str]:
        lines: list[str] = []
        for item in self._skills:
            definition = item.definition
            lines.append(
                f"{definition.name} | domain={definition.domain} | risk={definition.risk_level} | "
                f"approval={definition.requires_approval} | {definition.description}"
            )
        return lines

    def get(self, name: str) -> BaseSkill | None:
        return self._by_name.get(name)

    def select_rule_based(self, *, message: str, context: Mapping[str, Any] | None = None) -> SkillSelection:
        context_map = context or {}
        domain_hint = self._infer_domain_hint(message=message, context=context_map)

        candidates: list[tuple[int, int, str, BaseSkill, SkillMatch]] = []
        for skill in self._skills:
            match = skill.evaluate(message=message, context=context_map)
            adjusted_score = match.score

            if domain_hint is not None:
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
        if domain_hint == "warehouse":
            return self._by_name["inventory_exception_skill"]
        return self._by_name["order_status_explain_skill"]

    @staticmethod
    def _infer_domain_hint(*, message: str, context: Mapping[str, Any]) -> SkillDomain | None:
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
