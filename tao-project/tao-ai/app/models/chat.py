from __future__ import annotations

import httpx

from app.config import settings
from app.models.ollama_provider import OllamaProvider


class ChatService:
    def __init__(self, provider: OllamaProvider) -> None:
        self.provider = provider

    async def generate(self, *, system_prompt: str, user_message: str, context: str = "") -> str:
        prompt = user_message.strip()
        if context.strip():
            prompt = f"{prompt}\n\n上下文证据:\n{context.strip()}"

        if self.provider.chat_model is not None:
            response = await self.provider.chat_model.ainvoke(
                [("system", system_prompt), ("human", prompt)]
            )
            content = getattr(response, "content", "")
            if isinstance(content, list):
                return "\n".join(str(item) for item in content)
            return str(content)

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
