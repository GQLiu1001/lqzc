"""提供与Agent相关的实现。"""

from __future__ import annotations

from app.models.chat import ChatService


class WarehouseAgent:
    """表示仓储Agent，负责根据提示词、上下文和工具结果生成回答。"""
    def __init__(self, chat_service: ChatService) -> None:
        """初始化仓储Agent，把运行时依赖和基础状态准备好。"""
        self.chat_service = chat_service

    async def answer(
        self,
        *,
        message: str,
        context: str,
    ) -> str:
        """基于消息、上下文和额外约束生成最终回答。"""
        prompt_parts = [
            "你是仓储域 Agent。重点解释库存状态、仓储流程和处理建议。",
            "不要直接执行高风险动作，只能给出建议或审批提示。",
        ]

        return await self.chat_service.generate(
            system_prompt="\n".join(prompt_parts),
            user_message=message,
            context=context,
        )
