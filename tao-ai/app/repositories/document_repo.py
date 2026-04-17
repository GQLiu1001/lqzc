from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from app.rag.chunker import chunk_document
from app.rag.constants import CHUNK_CACHE_PATH, SUPPORTED_DOC_SUFFIXES, default_knowledge_sources
from app.rag.parser import parse_document


class IndexedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    content: str
    domain: str
    scene: str | None = None
    source_type: str
    version: str | None = None
    effective_at: str | None = None
    metadata: dict = Field(default_factory=dict)


_index_cache: list[IndexedChunk] | None = None
_index_signature: tuple[tuple[str, float], ...] | None = None


def load_indexed_chunks(force_refresh: bool = False) -> list[IndexedChunk]:
    global _index_cache, _index_signature

    signature = source_signature()
    if not force_refresh and _index_cache is not None and _index_signature == signature:
        return _index_cache

    chunks: list[IndexedChunk] = []
    for source, file_path in iter_source_files():
        parsed = parse_document(file_path, source)
        if parsed is None:
            continue
        chunks.extend(IndexedChunk.model_validate(item) for item in chunk_document(parsed))

    _index_cache = chunks
    _index_signature = signature
    _save_cache(chunks)
    return chunks


def describe_index() -> dict:
    chunks = load_indexed_chunks()
    by_domain: dict[str, int] = {}
    docs: set[str] = set()
    for chunk in chunks:
        docs.add(chunk.doc_id)
        by_domain[chunk.domain] = by_domain.get(chunk.domain, 0) + 1
    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "domains": by_domain,
        "cachePath": str(CHUNK_CACHE_PATH),
    }


def iter_source_files() -> Iterable[tuple[object, Path]]:
    for source in default_knowledge_sources():
        if not source.root.exists():
            continue
        for path in sorted(source.root.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if path.suffix.lower() not in SUPPORTED_DOC_SUFFIXES:
                continue
            yield source, path


def source_signature() -> tuple[tuple[str, float], ...]:
    rows: list[tuple[str, float]] = []
    for _, path in iter_source_files():
        try:
            rows.append((str(path), path.stat().st_mtime))
        except FileNotFoundError:
            continue
    return tuple(rows)


def load_cached_chunks() -> list[IndexedChunk]:
    if not CHUNK_CACHE_PATH.exists():
        return []
    raw = json.loads(CHUNK_CACHE_PATH.read_text(encoding="utf-8"))
    return [IndexedChunk.model_validate(item) for item in raw]


def _save_cache(chunks: list[IndexedChunk]) -> None:
    CHUNK_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHUNK_CACHE_PATH.write_text(
        json.dumps([chunk.model_dump(mode="json") for chunk in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
