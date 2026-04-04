"""提供与重排器相关的实现。"""

from __future__ import annotations


def rerank_hits(hits: list[dict]) -> list[dict]:
    """对候选rerankHITS结果重新排序，把更相关的内容排在前面。"""
    return sorted(hits, key=lambda item: float(item.get("score", 0.0)), reverse=True)

