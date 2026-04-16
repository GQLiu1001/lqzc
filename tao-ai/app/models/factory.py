"""模型工厂:按 provider 返回 chat / embedding 实例。

M1 仅接入 Ollama;预留参数以便 M2 切换到 OpenAI-compatible / vLLM 等。
"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.models.ollama_provider import get_chat_model, get_embedding_model


def make_chat(temperature: float = 0.2) -> BaseChatModel:
    return get_chat_model(temperature=temperature)


def make_embeddings() -> Embeddings:
    return get_embedding_model()
