from __future__ import annotations

import math
import re

from app.rag.constants import DEFAULT_RECALL_K, MIN_RETRIEVAL_SCORE, SCENE_HINTS
from app.repositories.document_repo import IndexedChunk
from app.schemas.rag import RAGSearchRequest, RetrievedChunk

_ASCII_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_\-/.]{1,}", re.IGNORECASE)
_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}")


def rewrite_query(query: str, domain: str, scene: str) -> str:
    normalized = normalize_query(query)
    hints = list(SCENE_HINTS.get(scene, ()))
    if domain == "warehouse" and "仓库" not in normalized:
        hints.append("仓库")
    if domain == "mall" and "商城" not in normalized:
        hints.append("商城")
    if not hints:
        return normalized
    hint_text = " ".join(dict.fromkeys(hints))
    if hint_text and hint_text not in normalized:
        return f"{normalized} {hint_text}".strip()
    return normalized


def recall_candidates(
    req: RAGSearchRequest,
    chunks: list[IndexedChunk],
    rewritten_query: str,
) -> list[RetrievedChunk]:
    query_tokens = tokenize(rewritten_query)
    if not query_tokens:
        return []

    recall_k = max(req.top_k, DEFAULT_RECALL_K)
    scored: list[RetrievedChunk] = []

    for chunk in chunks:
        score = lexical_score(rewritten_query, query_tokens, chunk)
        if score < MIN_RETRIEVAL_SCORE:
            continue
        scored.append(
            RetrievedChunk(
                doc_id=chunk.doc_id,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                content=chunk.content,
                score=round(score, 6),
                domain=chunk.domain,
                scene=chunk.scene,
                source_type=chunk.source_type,
                version=chunk.version,
                effective_at=_parse_effective_at(chunk.effective_at),
                metadata=chunk.metadata,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:recall_k]


def normalize_query(query: str) -> str:
    normalized = (query or "").strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def tokenize(text: str) -> set[str]:
    normalized = normalize_query(text)
    tokens: set[str] = set(_ASCII_TOKEN_PATTERN.findall(normalized))

    for run in _CJK_PATTERN.findall(normalized):
        tokens.add(run)
        for size in (2, 3):
            if len(run) < size:
                continue
            for index in range(0, len(run) - size + 1):
                tokens.add(run[index:index + size])

    return {token for token in tokens if len(token.strip()) >= 2}


def lexical_score(query: str, query_tokens: set[str], chunk: IndexedChunk) -> float:
    content_tokens = tokenize(chunk.content)
    title_tokens = tokenize(chunk.title)
    if not content_tokens and not title_tokens:
        return 0.0

    overlap = query_tokens.intersection(content_tokens)
    title_overlap = query_tokens.intersection(title_tokens)

    overlap_ratio = len(overlap) / max(len(query_tokens), 1)
    title_ratio = len(title_overlap) / max(len(query_tokens), 1)

    phrase_bonus = 0.18 if query and query in normalize_query(chunk.content) else 0.0
    scene_bonus = 0.12 if chunk.scene and chunk.scene != "general" and chunk.scene in query else 0.0
    metadata_bonus = 0.08 if any(token in str(chunk.metadata).lower() for token in query_tokens) else 0.0

    score = overlap_ratio * 0.62 + title_ratio * 0.22 + phrase_bonus + scene_bonus + metadata_bonus
    if overlap:
        score += min(math.log(len(overlap) + 1, 10), 0.1)
    return min(score, 1.0)


def _parse_effective_at(value: str | None):
    if not value:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(value)
    except ValueError:
        return None
