from __future__ import annotations

import logging
from time import perf_counter

from app.core.config import settings
from app.core.trace import trace_out
from app.rag import cross_reranker
from app.rag.constants import MIN_RERANK_SCORE
from app.rag.retriever import normalize_query, tokenize
from app.schemas.rag import RetrievedChunk

logger = logging.getLogger(__name__)

_CROSS_WEIGHT = 0.7
_LEXICAL_WEIGHT = 0.3
_CROSS_CANDIDATE_CAP = 12


def _lexical_rerank(query: str, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
    if not hits:
        return []

    normalized_query = normalize_query(query)
    query_tokens = tokenize(normalized_query)
    reranked: list[RetrievedChunk] = []

    for hit in hits:
        content = normalize_query(hit.content)
        title = normalize_query(hit.title)
        content_tokens = tokenize(content)
        title_tokens = tokenize(title)

        exact_bonus = 0.24 if normalized_query and normalized_query in content else 0.0
        title_bonus = 0.18 if normalized_query and normalized_query in title else 0.0
        overlap_ratio = len(query_tokens.intersection(content_tokens)) / max(len(query_tokens), 1)
        title_ratio = len(query_tokens.intersection(title_tokens)) / max(len(query_tokens), 1)
        metadata_bonus = 0.08 if any(token in str(hit.metadata).lower() for token in query_tokens) else 0.0

        rerank_score = min(
            hit.score * 0.55 + overlap_ratio * 0.2 + title_ratio * 0.1 + exact_bonus + title_bonus + metadata_bonus,
            1.0,
        )
        if rerank_score < MIN_RERANK_SCORE:
            continue

        reranked.append(hit.model_copy(update={"rerank_score": round(rerank_score, 6)}))

    reranked.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
    return reranked


def rerank_hits(query: str, hits: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """同步路径：仅走词面 rerank。兼容现有调用点。"""
    return _lexical_rerank(query, hits)[:top_k]


async def rerank_hits_async(
    query: str,
    hits: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    """异步路径：词面 rerank → 可选 cross-encoder 重排。"""
    lexical = _lexical_rerank(query, hits)
    if not lexical:
        return []

    mode = (settings.rag_reranker_mode or "lexical").lower()
    if mode != "qwen":
        return lexical[:top_k]

    candidates = lexical[:_CROSS_CANDIDATE_CAP]
    started = perf_counter()
    scores = await cross_reranker.score_pairs(query, [c.content for c in candidates])
    yes_count = sum(1 for s in scores if s and s >= 0.5)
    no_count = sum(1 for s in scores if s is not None and s < 0.5)
    miss_count = sum(1 for s in scores if s is None)
    trace_out(
        "rerank.cross",
        None,
        elapsed_ms=int((perf_counter() - started) * 1000),
        model=settings.rag_reranker_model,
        candidates=len(candidates),
        yes=yes_count,
        no=no_count,
        miss=miss_count,
    )

    merged: list[RetrievedChunk] = []
    for hit, cross_score in zip(candidates, scores, strict=True):
        lexical_component = hit.rerank_score or 0.0
        if cross_score is None:
            final = lexical_component
        else:
            final = round(_CROSS_WEIGHT * cross_score + _LEXICAL_WEIGHT * lexical_component, 6)
        merged.append(hit.model_copy(update={"rerank_score": final}))

    merged.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
    return merged[:top_k]
