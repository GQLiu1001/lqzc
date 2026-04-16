"""Ollama chat / embedding 封装。"""
from __future__ import annotations

from functools import lru_cache

from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.config import get_settings


@lru_cache(maxsize=4)
def get_chat_model(temperature: float = 0.2) -> ChatOllama:
    s = get_settings()
    return ChatOllama(
        model=s.ollama_chat_model,
        base_url=s.ollama_base_url,
        temperature=temperature,
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> OllamaEmbeddings:
    s = get_settings()
    return OllamaEmbeddings(
        model=s.ollama_embed_model,
        base_url=s.ollama_base_url,
    )
