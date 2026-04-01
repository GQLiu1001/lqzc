from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class StockHoldReleaseSkill(BaseSkill):
    definition = SkillDefinition(
        name="stock_hold_release_skill",
        domain="warehouse",
        retrieval_domain="business_rules",
        description="处理库存冻结、释放、锁库和库存调整建议（高风险）。",
        risk_level="HIGH",
        requires_approval=True,
        priority=5,
        keyword_weights=(
            ("冻结", 12),
            ("解冻", 12),
            ("释放", 10),
            ("锁库", 12),
            ("库存调整", 12),
            ("扣减", 10),
            ("回滚库存", 10),
        ),
        tool_hints=("submit_inventory_adjustment_for_approval",),
        system_instruction=(
            "仅给出风险评估和审批建议，禁止直接确认已执行库存变更。"
        ),
        response_contract=(
            "输出必须包含风险说明、审批要求、影响范围评估。"
        ),
    )
