"""提供与检索器factory相关的实现。"""

from __future__ import annotations

import logging

from app.config import settings
from app.models.embedding import EmbeddingService
from app.retrieval.collections import collection_for_domain
from app.retrieval.filters import metadata_filter
from app.retrieval.milvus_client import MilvusClient
from app.retrieval.reranker import rerank_hits


logger = logging.getLogger(__name__)


class MilvusRetriever:
    """Milvus 检索器封装。

    它把一次 RAG 检索拆成了几步固定动作：
    1. 先根据业务域决定该查哪个 collection
    2. 把用户问题转成向量
    3. 调用 Milvus 做向量搜索
    4. 对结果再做一次轻量重排
    """
    def __init__(self, *, embedding_service: EmbeddingService, milvus_client: MilvusClient) -> None:
        """初始化milvus检索器，把运行时依赖和基础状态准备好。"""
        self.embedding_service = embedding_service
        self.milvus_client = milvus_client

    def search(self, *, query: str, domain: str, tenant_id: str | None = None, top_k: int | None = None) -> tuple[str, list[dict]]:
        """执行一次完整的知识检索。

        这里虽然代码不长，但逻辑很完整：
        - `collection_for_domain` 负责把业务域映射到具体知识库
        - `embed_query` 负责把问题转成向量
        - `metadata_filter` 负责按租户等条件裁剪范围
        - `rerank_hits` 负责把更像答案的片段排到前面
        """
        collection_name = collection_for_domain(domain)
        try:
            # 先把自然语言问题转成向量，向量库才能做相似度搜索。
            vector = self.embedding_service.embed_query(query)
            # 如果 collection 不存在或维度不匹配，这里会自动补齐。
            self.milvus_client.ensure_collection(collection_name, dim=len(vector))
            expr = metadata_filter(tenant_id=tenant_id)
            hits = self.milvus_client.search(
                collection_name=collection_name,
                query_vector=vector,
                top_k=top_k or settings.rag_top_k,
                expr=expr or None,
            )
            return collection_name, rerank_hits(hits)
        except Exception as exc:
            # 检索失败时不直接让整个对话崩掉，而是回退成“无证据继续回答”。
            logger.warning("retrieval skipped: %s", exc)
            return collection_name, []
