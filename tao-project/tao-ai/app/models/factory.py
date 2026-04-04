"""提供与factory相关的实现。"""

from __future__ import annotations

from app.models.chat import ChatService
from app.models.embedding import EmbeddingService
from app.models.ollama_provider import OllamaProvider


class ModelFactory:
    """模型相关对象的创建工厂。

    这个类的意义在于把“模型底层提供器”和“上层服务对象”隔离开：
    - 底层 provider 负责接 Ollama / LangChain
    - 上层 ChatService / EmbeddingService 负责给业务层一个更稳定的接口
    """
    def __init__(self) -> None:
        """创建底层模型提供器。"""
        self.provider = OllamaProvider()

    def create_chat_service(self) -> ChatService:
        """创建聊天服务封装。"""
        return ChatService(self.provider)

    def create_embedding_service(self) -> EmbeddingService:
        """创建向量化服务封装。"""
        return EmbeddingService(self.provider)
