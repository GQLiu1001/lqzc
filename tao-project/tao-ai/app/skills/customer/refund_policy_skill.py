"""提供与退款规则技能相关的实现。"""

from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class RefundPolicySkill(BaseSkill):
    """定义退款规则技能，用于判断当前用户问题是否适合走这项业务技能。"""
    definition = SkillDefinition(
        name="refund_policy_skill",
        domain="customer_service",
        retrieval_domain="customer_policy",
        description="处理退款、退货、补偿规则解释和退款申请前置校验。",
        risk_level="HIGH",
        requires_approval=True,
        priority=5,
        keyword_weights=(
            ("退款", 12),
            ("退货", 11),
            ("补偿", 10),
            ("赔付", 10),
            ("仅退款", 11),
            ("售后政策", 8),
        ),
        tool_hints=("submit_refund_for_approval", "get_order_detail"),
        system_instruction=(
            "明确区分“规则说明”和“真实执行动作”。任何退款承诺都要先说明需审批。"
        ),
        response_contract=(
            "输出包含：是否支持、所需材料、审批说明、预计处理时效。"
        ),
    )
