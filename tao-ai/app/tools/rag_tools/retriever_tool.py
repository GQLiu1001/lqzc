"""RAG Tool — M3 重构。

use_stub_stores=True  → InMemoryStore (numpy cosine, 种子文档)
use_stub_stores=False → Milvus ANN 检索 + LLM Rerank

@tool 接口不变, 返回 RetrievalHit 列表。
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from langchain_core.tools import tool

from app.config import get_settings
from app.models.factory import make_embeddings
from app.observability.metrics import observe_rag_hits
from app.retrieval.indexing import SEED_DOCS
from app.schemas.tool import RetrievalHit

logger = logging.getLogger(__name__)


# ── InMemory 实现 (stub) ──────────────────────────────────

class _InMemoryStore:
    def __init__(self) -> None:
        self._embedder = make_embeddings()
        self._vectors: Optional[np.ndarray] = None
        self._docs: list[dict] = []

    def _ensure_indexed(self) -> None:
        if self._vectors is not None:
            return
        texts = [d["text"] for d in SEED_DOCS]
        logger.info("rag_stub: embedding %d seed docs", len(texts))
        vecs = self._embedder.embed_documents(texts)
        self._vectors = np.array(vecs, dtype=np.float32)
        self._docs = list(SEED_DOCS)

    def search(self, query: str, top_k: int, source: Optional[str] = None) -> list[RetrievalHit]:
        self._ensure_indexed()
        qv = np.array(self._embedder.embed_query(query), dtype=np.float32)
        norms = np.linalg.norm(self._vectors, axis=1) * np.linalg.norm(qv) + 1e-9
        sims = (self._vectors @ qv) / norms

        ranked = sorted(
            zip(self._docs, sims.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )
        hits: list[RetrievalHit] = []
        for doc, score in ranked:
            if source and doc["source"] != source:
                continue
            hits.append(
                RetrievalHit(
                    doc_id=doc["doc_id"],
                    score=float(score),
                    text=doc["text"],
                    source=doc["source"],
                )
            )
            if len(hits) >= top_k:
                break
        return hits


_mem_store: Optional[_InMemoryStore] = None


def _get_mem_store() -> _InMemoryStore:
    global _mem_store
    if _mem_store is None:
        _mem_store = _InMemoryStore()
    return _mem_store


# ── Milvus 实现 ───────────────────────────────────────────

def _search_milvus(query: str, top_k: int, source: Optional[str] = None) -> list[RetrievalHit]:
    from app.retrieval.collections import get_source_collection_map
    from app.retrieval.milvus_client import get_milvus_client

    s = get_settings()
    client = get_milvus_client()
    embedder = make_embeddings()
    source_map = get_source_collection_map()
    qv = embedder.embed_query(query)

    expand = s.rerank_expand_factor if s.enable_rerank else 1
    search_k = top_k * expand

    if source and source in source_map:
        collections = [source_map[source]]
    else:
        collections = list(source_map.values())

    all_hits: list[RetrievalHit] = []
    for coll_name in collections:
        try:
            results = client.search(
                collection_name=coll_name,
                data=[qv],
                limit=search_k,
                output_fields=["doc_id", "text", "source"],
                anns_field="embedding",
            )
            for res_list in results:
                for item in res_list:
                    entity = item.get("entity", item)
                    all_hits.append(RetrievalHit(
                        doc_id=entity.get("doc_id", ""),
                        score=float(item.get("distance", 0.0)),
                        text=entity.get("text", ""),
                        source=entity.get("source", ""),
                    ))
        except Exception as exc:
            logger.warning("milvus search failed on %s: %s", coll_name, exc)

    all_hits.sort(key=lambda h: h.score, reverse=True)
    return all_hits[:search_k]


# ── 统一入口 ──────────────────────────────────────────────

@tool("rag_search", return_direct=False)
async def rag_search(query: str, source: Optional[str] = None) -> list[dict]:
    """检索知识库, 返回与 query 最相似的文档片段。

    Args:
        query: 自然语言问题。
        source: 可选, 限定在某一类文档 (customer_faq / customer_policy / warehouse_sop)。
    """
    s = get_settings()
    top_k = s.rag_top_k

    if s.use_stub_stores:
        hits = _get_mem_store().search(query, top_k=top_k, source=source)
        observe_rag_hits(len(hits), mode="stub")
    else:
        raw_hits = _search_milvus(query, top_k=top_k, source=source)
        if s.enable_rerank and len(raw_hits) > top_k:
            from app.retrieval.reranker import rerank
            hits = await rerank(query, raw_hits, top_k)
        else:
            hits = raw_hits[:top_k]
        observe_rag_hits(len(hits), mode="milvus")

    return [h.model_dump() for h in hits]
