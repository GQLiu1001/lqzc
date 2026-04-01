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
    def __init__(self, *, embedding_service: EmbeddingService, milvus_client: MilvusClient) -> None:
        self.embedding_service = embedding_service
        self.milvus_client = milvus_client

    def search(self, *, query: str, domain: str, tenant_id: str | None = None, top_k: int | None = None) -> tuple[str, list[dict]]:
        collection_name = collection_for_domain(domain)
        try:
            vector = self.embedding_service.embed_query(query)
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
            logger.warning("retrieval skipped: %s", exc)
            return collection_name, []
