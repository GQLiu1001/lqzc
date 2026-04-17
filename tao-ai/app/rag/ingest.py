from __future__ import annotations

import asyncio
import json

from app.repositories.document_repo import describe_index, load_indexed_chunks
from app.repositories.milvus_repo import get_milvus_repository


async def ingest_default_corpus(force_refresh: bool = False) -> dict:
    chunks = await asyncio.to_thread(load_indexed_chunks, force_refresh)
    index_summary = await asyncio.to_thread(describe_index)
    milvus_result = await get_milvus_repository().index_chunks([chunk.model_dump(mode="json") for chunk in chunks])
    return {
        **index_summary,
        "forceRefresh": force_refresh,
        "milvus": milvus_result,
    }


async def main() -> None:
    result = await ingest_default_corpus(force_refresh=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
