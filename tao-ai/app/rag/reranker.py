from __future__ import annotations

from app.rag.constants import MIN_RERANK_SCORE
from app.rag.retriever import normalize_query, tokenize
from app.schemas.rag import RetrievedChunk


def rerank_hits(query: str, hits: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
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
    return reranked[:top_k]
