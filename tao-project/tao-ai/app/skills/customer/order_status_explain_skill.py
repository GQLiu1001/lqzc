from __future__ import annotations

from app.skills.base import BaseSkill, RegexSignal, SkillDefinition


class OrderStatusExplainSkill(BaseSkill):
    definition = SkillDefinition(
        name="order_status_explain_skill",
        domain="customer_service",
        retrieval_domain="customer_service",
        description="解释订单进度、物流状态、发货时效和催单问题。",
        risk_level="LOW",
        requires_approval=False,
        priority=10,
        default_skill_for_domain=True,
        keyword_weights=(
            ("订单", 10),
            ("发货", 9),
            ("物流", 9),
            ("快递", 8),
            ("签收", 7),
            ("催单", 7),
            ("进度", 5),
        ),
        regex_signals=(
            RegexSignal(
                pattern=r"(?<![A-Za-z0-9-])([A-Za-z]{0,4}\d{6,20}[A-Za-z0-9-]*)(?![A-Za-z0-9-])",
                weight=8,
                label="order_no_like",
            ),
        ),
        tool_hints=("get_order_detail",),
        system_instruction=(
            "优先基于订单事实和时间线回答。若缺少订单号，先提示用户补充订单号再给结论。"
        ),
        response_contract=(
            "回答包含：当前状态、原因解释、下一步建议。不要编造发货时间。"
        ),
    )
