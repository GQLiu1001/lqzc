"""提供与补货建议技能相关的实现。"""

from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class ReplenishmentSuggestionSkill(BaseSkill):
    """定义补货建议技能，用于判断当前用户问题是否适合走这项业务技能。"""
    definition = SkillDefinition(
        name="replenishment_suggestion_skill",
        domain="warehouse",
        retrieval_domain="historical_cases",
        description="给出补货建议、补仓优先级、安全库存相关建议。",
        risk_level="MEDIUM",
        requires_approval=False,
        priority=15,
        keyword_weights=(
            ("补货", 12),
            ("补仓", 11),
            ("再订货", 11),
            ("采购建议", 10),
            ("安全库存", 10),
            ("预警", 8),
            ("周转", 7),
        ),
        tool_hints=("search_inventory",),
        system_instruction=(
            "先描述当前库存风险，再给可执行补货建议，避免直接触发库存写操作。"
        ),
        response_contract=(
            "输出包含：缺口判断、优先级、建议补货量区间、执行建议。"
        ),
    )
