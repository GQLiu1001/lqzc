from __future__ import annotations

from app.skills.base import BaseSkill, RegexSignal, SkillDefinition


class InventoryExceptionSkill(BaseSkill):
    definition = SkillDefinition(
        name="inventory_exception_skill",
        domain="warehouse",
        retrieval_domain="warehouse",
        description="处理库存数量、库存异常、有货/缺货状态和型号库存查询。",
        risk_level="MEDIUM",
        requires_approval=False,
        priority=10,
        default_skill_for_domain=True,
        keyword_weights=(
            ("库存", 12),
            ("有货", 10),
            ("现货", 10),
            ("缺货", 10),
            ("库存数", 11),
            ("库存异常", 12),
            ("可售", 8),
        ),
        regex_signals=(
            RegexSignal(
                pattern=r"(?<![A-Za-z0-9-])([A-Za-z]{1,6}[0-9]{2,}[A-Za-z0-9-]*)(?![A-Za-z0-9-])",
                weight=9,
                label="item_model_like",
            ),
        ),
        tool_hints=("get_inventory_by_model", "search_inventory"),
        system_instruction=(
            "优先返回库存事实数据（数量、型号、规格、仓库）。没有命中型号时再给分页库存概览。"
        ),
        response_contract=(
            "若命中具体型号，第一句必须给出库存总数。不要把建议当作已执行动作。"
        ),
    )
