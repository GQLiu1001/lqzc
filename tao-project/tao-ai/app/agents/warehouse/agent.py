from __future__ import annotations

from app.models.chat import ChatService


class WarehouseAgent:
    def __init__(self, chat_service: ChatService) -> None:
        self.chat_service = chat_service

    async def answer(
        self,
        *,
        message: str,
        context: str,
        skill_instruction: str = "",
        response_contract: str = "",
    ) -> str:
        prompt_parts = [
            "你是仓储域 Agent。重点解释库存状态、仓储流程和处理建议。",
            "不要直接执行高风险动作，只能给出建议或审批提示。",
        ]
        if skill_instruction.strip():
            prompt_parts.append(f"当前技能执行要求：{skill_instruction.strip()}")
        if response_contract.strip():
            prompt_parts.append(f"输出约束：{response_contract.strip()}")

        return await self.chat_service.generate(
            system_prompt="\n".join(prompt_parts),
            user_message=message,
            context=context,
        )
