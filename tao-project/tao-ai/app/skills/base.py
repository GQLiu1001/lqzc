from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Literal
import re


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SkillDomain = Literal["customer_service", "warehouse"]


@dataclass(frozen=True, slots=True)
class RegexSignal:
    pattern: str
    weight: int
    label: str


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    name: str
    domain: SkillDomain
    retrieval_domain: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    version: str = "1.0.0"
    priority: int = 100
    default_skill_for_domain: bool = False
    keyword_weights: tuple[tuple[str, int], ...] = ()
    regex_signals: tuple[RegexSignal, ...] = ()
    tool_hints: tuple[str, ...] = ()
    system_instruction: str = ""
    response_contract: str = ""


@dataclass(frozen=True, slots=True)
class SkillMatch:
    skill_name: str
    score: int
    reason: str
    signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SkillSelection:
    definition: SkillDefinition
    match: SkillMatch
    route_source: Literal["rule", "llm"]
    route_confidence: float | None = None


class BaseSkill:
    definition: SkillDefinition

    def __init__(self) -> None:
        self._compiled_regex_rules = [
            (re.compile(item.pattern, flags=re.IGNORECASE), item.weight, item.label)
            for item in self.definition.regex_signals
        ]

    def evaluate(self, *, message: str, context: Mapping[str, Any] | None = None) -> SkillMatch:
        lowered = message.lower()
        score = 0
        signals: list[str] = []

        for token, weight in self.definition.keyword_weights:
            if token.lower() in lowered:
                score += weight
                signals.append(f"kw:{token}")

        for pattern, weight, label in self._compiled_regex_rules:
            if pattern.search(message):
                score += weight
                signals.append(f"re:{label}")

        score += self._context_bonus(context=context or {})
        if score <= 0 and self.definition.default_skill_for_domain:
            score = 1
            signals.append("fallback:default")

        reason = ", ".join(signals) if signals else "no strong lexical signal"
        return SkillMatch(
            skill_name=self.definition.name,
            score=score,
            reason=reason,
            signals=tuple(signals),
        )

    def _context_bonus(self, *, context: Mapping[str, Any]) -> int:
        channel = str(context.get("channel") or "").lower()
        if not channel:
            return 0

        if self.definition.domain == "warehouse" and "warehouse" in channel:
            return 4
        if self.definition.domain == "customer_service" and any(tag in channel for tag in ("customer", "service", "support")):
            return 4
        return 0
