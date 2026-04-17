from __future__ import annotations

import asyncio
from functools import lru_cache
from time import perf_counter

from app.core.config import settings
from app.core.trace import trace_in, trace_out
from app.rag import filters, formatter, reranker, retriever
from app.repositories.document_repo import describe_index, load_indexed_chunks
from app.repositories.milvus_repo import get_milvus_repository
from app.schemas.rag import RAGSearchRequest, RAGSearchResult, RetrievedChunk


class RAGService:

    async def search(self, req: RAGSearchRequest) -> RAGSearchResult:
        started = perf_counter()

        query = (req.query or "").strip()
        trace_in(
            "rag.search",
            session_id=req.session_id,
            domain=req.domain,
            scene=req.scene or "general",
            query=query,
            top_k=req.top_k,
            user_context=req.user_context,
        )
        if not query:
            result = RAGSearchResult(
                success=False,
                query=req.query,
                no_hit=True,
                message="请提供检索问题",
                error_code="MISSING_QUERY",
            )
            trace_out("rag.search", result, elapsed_ms=int((perf_counter() - started) * 1000))
            return result

        normalized_req = req.model_copy(
            update={
                "top_k": max(1, min(req.top_k or settings.rag_default_top_k, 10)),
                "scene": req.scene or "general",
            }
        )

        used_filters = filters.build_used_filters(normalized_req)
        rewritten_query = retriever.rewrite_query(query, normalized_req.domain, normalized_req.scene)

        indexed_chunks = await asyncio.to_thread(load_indexed_chunks, False)
        filtered_chunks = filters.apply_metadata_filters(indexed_chunks, normalized_req)

        milvus_repo = get_milvus_repository()
        await milvus_repo.index_chunks([chunk.model_dump(mode="json") for chunk in indexed_chunks])
        milvus_hits = await milvus_repo.search(
            query=rewritten_query,
            top_k=normalized_req.top_k,
            filters=used_filters,
        )

        lexical_hits = retriever.recall_candidates(normalized_req, filtered_chunks, rewritten_query)
        merged_hits = _merge_hits(milvus_hits, lexical_hits)
        reranked = reranker.rerank_hits(query, merged_hits, normalized_req.top_k)
        search_mode = _resolve_search_mode(milvus_hits, lexical_hits)

        no_hit = not reranked
        context_text = formatter.build_context_pack(reranked)
        latency_ms = int((perf_counter() - started) * 1000)

        result = RAGSearchResult(
            success=not no_hit,
            query=query,
            rewritten_query=rewritten_query,
            hits=reranked,
            used_filters=used_filters,
            no_hit=no_hit,
            context_text=context_text,
            retrieved_docs_count=len(reranked),
            search_mode=search_mode,
            message="未检索到足够依据" if no_hit else "ok",
            latency_ms=latency_ms,
        )
        trace_out(
            "rag.search",
            result,
            elapsed_ms=latency_ms,
            rewritten_query=rewritten_query,
            used_filters=used_filters,
            indexed_chunks=len(indexed_chunks),
            filtered_chunks=len(filtered_chunks),
            milvus_hits=len(milvus_hits),
            lexical_hits=len(lexical_hits),
            merged_hits=len(merged_hits),
            reranked_hits=len(reranked),
            mode=search_mode,
        )
        return result

    async def corpus_summary(self) -> dict:
        summary = await asyncio.to_thread(describe_index)
        available, reason = get_milvus_repository().availability()
        summary["milvus"] = {"available": available, "message": reason}
        return summary


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()


def _merge_hits(milvus_hits: list[RetrievedChunk], lexical_hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
    merged: dict[str, RetrievedChunk] = {hit.chunk_id: hit for hit in lexical_hits}

    for dense_hit in milvus_hits:
        existing = merged.get(dense_hit.chunk_id)
        if existing is None:
            merged[dense_hit.chunk_id] = dense_hit
            continue

        blended_score = min(1.0, max(existing.score, dense_hit.score) + min(existing.score, dense_hit.score) * 0.15)
        merged[dense_hit.chunk_id] = existing.model_copy(
            update={
                "score": round(blended_score, 6),
                "metadata": {**dense_hit.metadata, **existing.metadata},
            }
        )

    return list(merged.values())


def _resolve_search_mode(milvus_hits: list[RetrievedChunk], lexical_hits: list[RetrievedChunk]) -> str:
    if milvus_hits and lexical_hits:
        return "hybrid"
    if milvus_hits:
        return "milvus-dense"
    return "local-lexical"
