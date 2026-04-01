from __future__ import annotations


def rerank_hits(hits: list[dict]) -> list[dict]:
    return sorted(hits, key=lambda item: float(item.get("score", 0.0)), reverse=True)

