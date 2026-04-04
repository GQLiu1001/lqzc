"""提供与routes文件相关的实现。"""

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
    """定义uploadresponse，用于约束接口入参与出参的数据结构。"""
    file_id: str
    original_name: str
    local_path: str
    status: str
    chunk_count: int
    indexed_count: int = 0
    index_error: str | None = None


_WHITESPACE = re.compile(r"\s+")


def _safe_filename(filename: str) -> str:
    """把上传文件名清洗成安全可落盘的名字。"""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
    return cleaned or "uploaded.txt"


def _decode_text(file_bytes: bytes) -> str:
    """尽量把上传的文本按常见中文编码解码出来。

    这里之所以要尝试 `utf-8 / gb18030 / gbk`，
    是因为业务资料经常来自不同系统导出，编码不一定统一。
    """
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return file_bytes.decode(encoding).replace("\r\n", "\n").replace("\r", "\n").strip()
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n").strip()


def _chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    """把长文本切成适合向量化和检索的小块。

    `overlap` 的作用是让相邻块之间保留一点重叠，
    避免一句完整语义刚好被切断后，两个块都不完整。
    """
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
    """上传文本文件并尝试写入知识库。

    这个接口做的事情其实不少：
    1. 接收文件并保存到本地
    2. 解码成文本
    3. 切块
    4. 做 embedding
    5. 写入 Milvus

    所以它本质上是一个“临时知识入库接口”。
    """
    file_id = uuid.uuid4().hex
    original_name = file.filename or "uploaded.txt"
    safe_name = _safe_filename(original_name)

    upload_root = settings.project_root / "data" / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    saved_name = f"{file_id}_{safe_name}"
    saved_path = upload_root / saved_name

    # 先完整读入文件，再同时完成本地保存和后续索引。
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

    # 上传成功后，并不是立刻可检索；还要先完成解码和切块。
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
            # 每个 chunk 都会生成一个向量，后面写进向量库。
            vectors = embedding_service.embed_documents(chunks)

            milvus_client = MilvusClient()
            rows = []
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False), start=1):
                # 每个 chunk 会带上 file_id、chunk_no、session_id 等元数据，方便后续过滤和回溯。
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

            # 当前上传文件统一写进 business_rules_collection。
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
            # 索引失败不影响上传成功，只是暂时无法检索到这份文档。
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
