from __future__ import annotations

from app.skills.base import BaseSkill, SkillDefinition


class CustomerReplyDraftSkill(BaseSkill):
    definition = SkillDefinition(
        name="customer_reply_draft_skill",
        domain="customer_service",
        retrieval_domain="customer_service",
        description="生成客服回复草稿、解释话术和沟通模板。",
        risk_level="LOW",
        requires_approval=False,
        priority=20,
        keyword_weights=(
            ("回复", 8),
            ("话术", 10),
            ("润色", 9),
            ("改写", 8),
            ("怎么回", 8),
            ("客服", 6),
            ("模板", 7),
        ),
        tool_hints=(),
        system_instruction=(
            "保持礼貌、清晰、可执行，避免超范围承诺。"
        ),
        response_contract=(
            "输出为可直接发送给客户的文案，并给出一句内部备注建议。"
        ),
    )
