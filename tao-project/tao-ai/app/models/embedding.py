"""提供与向量化相关的实现。"""

from __future__ import annotations

from app.models.ollama_provider import OllamaProvider


class EmbeddingService:
    """向量化服务封装。

    RAG 检索不是直接拿文本匹配，而是先把文本转成向量再做相似度搜索。
    这里就是负责调用底层 embedding 模型的地方。
    """
    def __init__(self, provider: OllamaProvider) -> None:
        """初始化向量化服务，把运行时依赖和基础状态准备好。"""
        self.provider = provider

    def embed_query(self, query: str) -> list[float]:
        """把单条查询语句转成向量。

        典型场景是：用户提了一个问题，需要拿这个问题去 Milvus 里查最像的知识片段。
        """
        return self.provider.embedding_model.embed_query(query)

    def embed_documents(self, docs: list[str]) -> list[list[float]]:
        """把多条文档一次性转成向量。

        典型场景是：构建知识库索引时，把一批文档先做 embedding 再写入向量库。
        """
        return self.provider.embedding_model.embed_documents(docs)
