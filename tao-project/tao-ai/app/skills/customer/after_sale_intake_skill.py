from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class AfterSaleIntakeSkill(BaseSkill):
    definition = SkillDefinition(
        name="after_sale_intake_skill",
        domain="customer_service",
        retrieval_domain="customer_policy",
        description="受理售后问题，收集必要材料并输出标准工单受理建议。",
        risk_level="MEDIUM",
        requires_approval=False,
        priority=15,
        keyword_weights=(
            ("售后", 11),
            ("破损", 9),
            ("质量问题", 10),
            ("少件", 8),
            ("漏发", 8),
            ("工单", 7),
            ("投诉", 8),
        ),
        tool_hints=("create_after_sale_ticket", "get_order_detail"),
        system_instruction=(
            "先判断是否属于售后受理范围，再告知需补充的证据和处理节点。"
        ),
        response_contract=(
            "输出包含：受理结论、材料清单、处理时限、下一步动作。"
        ),
    )
