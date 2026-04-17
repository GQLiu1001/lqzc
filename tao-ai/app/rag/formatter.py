from __future__ import annotations

from app.schemas.rag import RetrievedChunk


def build_context_pack(hits: list[RetrievedChunk]) -> str:
    if not hits:
        return ""

    blocks: list[str] = []
    for index, hit in enumerate(hits, start=1):
        score = hit.rerank_score if hit.rerank_score is not None else hit.score
        version = hit.version or "unknown"
        header = (
            f"[Doc#{index} | score={score:.3f} | title={hit.title} | "
            f"domain={hit.domain} | scene={hit.scene or 'general'} | version={version}]"
        )
        source_path = hit.metadata.get("relative_path") or hit.metadata.get("source_path")
        source_line = f"source={source_path}" if source_path else ""
        blocks.append("\n".join(part for part in [header, source_line, hit.content.strip()] if part))
    return "\n\n".join(blocks)


def summarize_hits(hits: list[RetrievedChunk]) -> list[dict]:
    return [
        {
            "doc_id": hit.doc_id,
            "chunk_id": hit.chunk_id,
            "title": hit.title,
            "score": hit.score,
            "rerank_score": hit.rerank_score,
            "domain": hit.domain,
            "scene": hit.scene,
            "source_type": hit.source_type,
            "version": hit.version,
            "metadata": hit.metadata,
        }
        for hit in hits
    ]
