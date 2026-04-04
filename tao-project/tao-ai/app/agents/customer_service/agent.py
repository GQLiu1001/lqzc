"""提供与Agent相关的实现。"""

from __future__ import annotations

from app.models.chat import ChatService


class CustomerServiceAgent:
    """表示客服服务Agent，负责根据提示词、上下文和工具结果生成回答。"""
    def __init__(self, chat_service: ChatService) -> None:
        """初始化客服服务Agent，把运行时依赖和基础状态准备好。"""
        self.chat_service = chat_service

    async def answer(
        self,
        *,
        message: str,
        context: str,
        skill_instruction: str = "",
        response_contract: str = "",
    ) -> str:
        """基于消息、上下文和额外约束生成最终回答。"""
        prompt_parts = [
            "你是客服域 Agent。你需要基于事实、检索证据和工具结果给出简洁回答。",
            "如果涉及退款或敏感动作，明确提示需要审批。",
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
