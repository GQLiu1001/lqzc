from __future__ import annotations

from app.models.ollama_provider import OllamaProvider


class EmbeddingService:
    def __init__(self, provider: OllamaProvider) -> None:
        self.provider = provider

    def embed_query(self, query: str) -> list[float]:
        return self.provider.embedding_model.embed_query(query)

    def embed_documents(self, docs: list[str]) -> list[list[float]]:
        return self.provider.embedding_model.embed_documents(docs)

