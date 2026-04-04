"""提供与基础相关的实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Literal
import re


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SkillDomain = Literal["customer_service", "warehouse"]


@dataclass(frozen=True, slots=True)
class RegexSignal:
    """一个正则触发信号。

    当用户消息命中某种模式时，可以为对应 skill 加上额外分数。
    """
    pattern: str
    weight: int
    label: str


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """一个 skill 的完整静态定义。

    这里描述的是“这个技能是什么、属于哪个域、风险多高、如何命中、建议用什么工具”。
    它本质上像一份配置，而不是运行时状态。
    """
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
    """某个 skill 针对当前输入算出来的匹配结果。"""
    skill_name: str
    score: int
    reason: str
    signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SkillSelection:
    """最终被选中的 skill 结果。"""
    definition: SkillDefinition
    match: SkillMatch
    route_source: Literal["rule", "llm"]
    route_confidence: float | None = None


class BaseSkill:
    """定义基础技能，用于判断当前用户问题是否适合走这项业务技能。"""
    definition: SkillDefinition

    def __init__(self) -> None:
        """初始化基础技能，把运行时依赖和基础状态准备好。"""
        # 先把正则编译好，避免每次 evaluate 时重复编译。
        self._compiled_regex_rules = [
            (re.compile(item.pattern, flags=re.IGNORECASE), item.weight, item.label)
            for item in self.definition.regex_signals
        ]

    def evaluate(self, *, message: str, context: Mapping[str, Any] | None = None) -> SkillMatch:
        """计算当前消息与本 skill 的匹配分数。

        评分来源主要有三块：
        - 关键词命中
        - 正则信号命中
        - 上下文加分
        """
        lowered = message.lower()
        score = 0
        signals: list[str] = []

        # 关键词适合做最直接、最便宜的粗判断。
        for token, weight in self.definition.keyword_weights:
            if token.lower() in lowered:
                score += weight
                signals.append(f"kw:{token}")

        # 正则适合识别更复杂的格式，比如订单号、型号、特定表达。
        for pattern, weight, label in self._compiled_regex_rules:
            if pattern.search(message):
                score += weight
                signals.append(f"re:{label}")

        score += self._context_bonus(context=context or {})
        if score <= 0 and self.definition.default_skill_for_domain:
            # 默认技能用于“本域都不太像，但总得给个保底处理模板”的场景。
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
        """根据额外上下文给 skill 加分。

        例如上游已经知道这条消息来自 warehouse channel，
        那仓储类 skill 就应该天然更有优势。
        """
        channel = str(context.get("channel") or "").lower()
        if not channel:
            return 0

        if self.definition.domain == "warehouse" and "warehouse" in channel:
            return 4
        if self.definition.domain == "customer_service" and any(tag in channel for tag in ("customer", "service", "support")):
            return 4
        return 0
