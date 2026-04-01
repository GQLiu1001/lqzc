from __future__ import annotations

from typing import Any

try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
except Exception:  # pragma: no cover - optional dependency fallback
    ChatOllama = None  # type: ignore[assignment]
    OllamaEmbeddings = None  # type: ignore[assignment]

from app.config import settings


class OllamaProvider:
    def __init__(self) -> None:
        self.langchain_available = ChatOllama is not None and OllamaEmbeddings is not None
        self._chat_model: Any = None
        self._embedding_model: Any = None

        if self.langchain_available:
            self._chat_model = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_chat_model,
                temperature=0.2,
            )
            self._embedding_model = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                model=settings.ollama_embed_model,
            )

    @property
    def chat_model(self) -> Any:
        return self._chat_model

    @property
    def embedding_model(self) -> Any:
        return self._embedding_model
