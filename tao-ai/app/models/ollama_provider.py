"""提供与ollama提供器相关的实现。"""

from __future__ import annotations

from typing import Any

try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
except Exception:  # pragma: no cover - optional dependency fallback
    ChatOllama = None  # type: ignore[assignment]
    OllamaEmbeddings = None  # type: ignore[assignment]

from app.config import settings


class OllamaProvider:
    """底层 Ollama / LangChain 提供器。

    它的职责不是给业务层直接用，而是负责准备好：
    - 聊天模型对象
    - 向量模型对象

    这样上层服务只需要关心“能不能聊天”“能不能做 embedding”，
    不需要关心具体依赖库是否安装、模型对象怎么初始化。
    """
    def __init__(self) -> None:
        """尝试初始化 LangChain-Ollama 相关对象。

        如果依赖不可用，系统不会立刻崩，而是允许上层走 HTTP fallback。
        这也是为什么 `ChatService` 里会再写一套原始 API 调用逻辑。
        """
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
        """返回聊天模型对象；如果不可用则返回空。"""
        return self._chat_model

    @property
    def embedding_model(self) -> Any:
        """返回向量模型对象；如果不可用则返回空。"""
        return self._embedding_model
