"""提供与仓储SOP检索技能相关的实现。"""

from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class WarehouseSopRetrievalSkill(BaseSkill):
    """定义仓储SOP检索技能，用于判断当前用户问题是否适合走这项业务技能。"""
    definition = SkillDefinition(
        name="warehouse_sop_retrieval_skill",
        domain="warehouse",
        retrieval_domain="warehouse",
        description="检索仓储 SOP、操作规范、入库出库流程。",
        risk_level="LOW",
        requires_approval=False,
        priority=20,
        keyword_weights=(
            ("sop", 11),
            ("流程", 8),
            ("操作规范", 10),
            ("入库", 9),
            ("出库", 9),
            ("拣货", 9),
            ("打包", 7),
            ("质检", 7),
        ),
        tool_hints=(),
        system_instruction=(
            "按步骤给出 SOP，必要时补充常见错误和检查点。"
        ),
        response_contract=(
            "输出使用步骤化结构，并标注适用场景和前置条件。"
        ),
    )
