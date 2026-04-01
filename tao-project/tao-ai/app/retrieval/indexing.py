"""Document indexing helpers.

This module is intentionally lightweight in the baseline refactor.
Use it as the extension point for bulk ingestion scripts.
"""

from __future__ import annotations

from app.retrieval.milvus_client import MilvusClient


def ensure_runtime_collections(client: MilvusClient, names: list[str], *, dim: int) -> None:
    for item in names:
        client.ensure_collection(item, dim=dim)

