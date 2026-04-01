from __future__ import annotations

from app.models.chat import ChatService
from app.models.embedding import EmbeddingService
from app.models.ollama_provider import OllamaProvider


class ModelFactory:
    def __init__(self) -> None:
        self.provider = OllamaProvider()

    def create_chat_service(self) -> ChatService:
        return ChatService(self.provider)

    def create_embedding_service(self) -> EmbeddingService:
        return EmbeddingService(self.provider)

