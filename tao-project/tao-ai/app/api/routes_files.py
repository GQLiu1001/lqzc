from __future__ import annotations

import logging
import re
import uuid

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.models.factory import ModelFactory
from app.retrieval.milvus_client import MilvusClient


router = APIRouter(tags=["files"])
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    file_id: str
    original_name: str
    local_path: str
    status: str
    chunk_count: int
    indexed_count: int = 0
    index_error: str | None = None


_WHITESPACE = re.compile(r"\s+")


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
    return cleaned or "uploaded.txt"


def _decode_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return file_bytes.decode(encoding).replace("\r\n", "\n").replace("\r", "\n").strip()
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n").strip()


def _chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    cleaned = _WHITESPACE.sub(" ", text).strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


@router.post("/files/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> UploadResponse:
    file_id = uuid.uuid4().hex
    original_name = file.filename or "uploaded.txt"
    safe_name = _safe_filename(original_name)

    upload_root = settings.project_root / "data" / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    saved_name = f"{file_id}_{safe_name}"
    saved_path = upload_root / saved_name

    file_bytes = await file.read()
    saved_path.write_bytes(file_bytes)
    await file.close()
    logger.info(
        "files.upload.received file_id=%s file=%s size_bytes=%s session_id=%s",
        file_id,
        original_name,
        len(file_bytes),
        session_id,
    )

    text = _decode_text(file_bytes)
    chunks = _chunk_text(text)
    logger.info(
        "files.upload.chunked file_id=%s chunks=%s",
        file_id,
        len(chunks),
    )

    indexed_count = 0
    index_error: str | None = None
    if chunks:
        try:
            model_factory = ModelFactory()
            embedding_service = model_factory.create_embedding_service()
            vectors = embedding_service.embed_documents(chunks)

            milvus_client = MilvusClient()
            rows = []
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False), start=1):
                rows.append(
                    {
                        "content": chunk,
                        "source": original_name,
                        "metadata": {
                            "file_id": file_id,
                            "chunk_no": idx,
                            "session_id": (session_id or "").strip() or None,
                            "doc_type": "uploaded_text",
                        },
                        "embedding": vector,
                    }
                )

            indexed_count = milvus_client.insert_chunks(
                collection_name=settings.business_rules_collection,
                rows=rows,
                dim=len(vectors[0]) if vectors else settings.milvus_embedding_dim,
            )
            logger.info(
                "files.upload.indexed file_id=%s indexed=%s collection=%s dim=%s",
                file_id,
                indexed_count,
                settings.business_rules_collection,
                (len(vectors[0]) if vectors else settings.milvus_embedding_dim),
            )
        except Exception as exc:
            index_error = str(exc)
            logger.warning("file upload indexed_count=0 because indexing failed: %s", exc)
            indexed_count = 0

    return UploadResponse(
        file_id=file_id,
        original_name=original_name,
        local_path=f"doc/{saved_name}",
        status="READY",
        chunk_count=len(chunks),
        indexed_count=indexed_count,
        index_error=index_error,
    )
