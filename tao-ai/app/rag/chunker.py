from __future__ import annotations

from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.rag.parser import ParsedDocument, stable_checksum

_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", "，", " ", ""],
    length_function=len,
)


def chunk_document(doc: ParsedDocument) -> list[dict]:
    pieces = _SPLITTER.split_text(doc.text)
    chunk_records: list[dict] = []

    for index, piece in enumerate(pieces, start=1):
        content = piece.strip()
        if not content:
            continue
        chunk_records.append(
            {
                "doc_id": doc.doc_id,
                "chunk_id": f"{doc.doc_id}#{index:03d}",
                "title": doc.title,
                "content": content,
                "domain": doc.domain,
                "scene": doc.scene,
                "source_type": doc.source_type,
                "version": doc.version,
                "effective_at": _to_iso(doc.effective_at),
                "metadata": {
                    **doc.metadata,
                    "access_level": doc.access_level,
                    "role_allowlist": list(doc.role_allowlist),
                    "warehouse_scope": list(doc.warehouse_scope),
                    "checksum": stable_checksum(content),
                },
            }
        )
    return chunk_records


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
