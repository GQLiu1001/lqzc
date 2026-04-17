from __future__ import annotations

import asyncio
import json
from time import perf_counter

from app.repositories.document_repo import describe_index, load_indexed_chunks
from app.core.trace import trace_in, trace_out
from app.repositories.milvus_repo import get_milvus_repository


async def ingest_default_corpus(force_refresh: bool = False) -> dict:
    started = perf_counter()
    trace_in("rag.ingest_default_corpus", force_refresh=force_refresh)
    chunks = await asyncio.to_thread(load_indexed_chunks, force_refresh)
    index_summary = await asyncio.to_thread(describe_index)
    milvus_result = await get_milvus_repository().index_chunks(
        [chunk.model_dump(mode="json") for chunk in chunks],
        force_refresh=force_refresh,
    )
    result = {
        **index_summary,
        "forceRefresh": force_refresh,
        "milvus": milvus_result,
    }
    trace_out(
        "rag.ingest_default_corpus",
        result,
        elapsed_ms=int((perf_counter() - started) * 1000),
        force_refresh=force_refresh,
        documents=index_summary.get("documents"),
        chunks=index_summary.get("chunks"),
        domains=index_summary.get("domains"),
        milvus=milvus_result,
    )
    return result


async def main() -> None:
    result = await ingest_default_corpus(force_refresh=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
