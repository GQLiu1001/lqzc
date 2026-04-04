"""提供与聊天相关的实现。"""

from __future__ import annotations

import httpx

from app.config import settings
from app.models.ollama_provider import OllamaProvider


class ChatService:
    """聊天模型调用封装。

    上层 Agent 不直接碰 LangChain/Ollama 细节，而是统一通过这里生成文本。
    这样以后如果要替换模型提供商，业务层改动会小很多。
    """
    def __init__(self, provider: OllamaProvider) -> None:
        """初始化聊天服务，把运行时依赖和基础状态准备好。"""
        self.provider = provider

    async def generate(self, *, system_prompt: str, user_message: str, context: str = "") -> str:
        """调用聊天模型生成文本。

        这里做了两件很关键的事：
        - 把检索/工具得到的上下文拼进用户问题
        - 优先走 LangChain 封装；如果没有可用对象，再走原始 HTTP 接口兜底

        所以它既是“提示词组装器”，也是“模型调用适配层”。
        """
        prompt = user_message.strip()
        if context.strip():
            # 上下文证据不会覆盖用户原话，而是追加到 prompt 后面，提醒模型“参考这些事实再回答”。
            prompt = f"{prompt}\n\n上下文证据:\n{context.strip()}"

        if self.provider.chat_model is not None:
            # LangChain 模式下，直接传消息数组，保持 system / human 角色分离。
            response = await self.provider.chat_model.ainvoke(
                [("system", system_prompt), ("human", prompt)]
            )
            content = getattr(response, "content", "")
            if isinstance(content, list):
                return "\n".join(str(item) for item in content)
            return str(content)

        # 如果 LangChain 适配不可用，则直接调用 Ollama HTTP API。
        chat_url = (
            f"{settings.ollama_base_url.rstrip('/')}/api/chat"
            if not settings.ollama_base_url.rstrip("/").endswith("/api")
            else f"{settings.ollama_base_url.rstrip('/')}/chat"
        )
        payload = {
            "model": settings.ollama_chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(chat_url, json=payload)
            response.raise_for_status()
            data = response.json()
        return str(((data.get("message") or {}).get("content")) or "")
