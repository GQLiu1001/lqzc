"""Document indexing helpers.

This module is intentionally lightweight in the baseline refactor.
Use it as the extension point for bulk ingestion scripts.
"""

from __future__ import annotations

from app.retrieval.milvus_client import MilvusClient


def ensure_runtime_collections(client: MilvusClient, names: list[str], *, dim: int) -> None:
    """确保ensureruntime集合满足执行条件，不满足时进行补救。"""
    for item in names:
        client.ensure_collection(item, dim=dim)

