"""PostgreSQL + pgvector storage for uploaded files and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
import re
import time
import uuid

import httpx
import psycopg
from psycopg.rows import dict_row


logger = logging.getLogger(__name__)
_WHITESPACE = re.compile(r"\s+")


@dataclass(slots=True)
class UploadResult:
    file_id: str
    original_name: str
    local_path: str
    status: str
    chunk_count: int


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    score: float
    file_name: str
    chunk_no: int


@dataclass(slots=True)
class SearchMetrics:
    top_k_requested: int
    top_k_returned: int
    fill_rate_at_k: float
    corpus_chunk_count: int
    corpus_file_count: int
    hit_file_count: int
    recall_proxy_at_k: float
    score_min: float
    score_max: float
    score_avg: float
    latency_ms: int


class PgVectorStore:
    """Own upload persistence and semantic retrieval for session documents."""

    def __init__(
        self,
        dsn: str,
        upload_dir: Path,
        ollama_base_url: str,
        embedding_model: str,
    ) -> None:
        self.dsn = dsn
        self.upload_dir = upload_dir
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.embedding_model = embedding_model
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _init_db(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_files (
                    id UUID PRIMARY KEY,
                    session_id TEXT,
                    original_name TEXT NOT NULL,
                    saved_name TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    mime_type TEXT,
                    size_bytes BIGINT,
                    sha256 CHAR(64),
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_file_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    file_id UUID NOT NULL REFERENCES ai_files(id) ON DELETE CASCADE,
                    chunk_no INT NOT NULL,
                    content TEXT NOT NULL,
                    token_count INT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    embedding VECTOR,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(file_id, chunk_no)
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_files_session_id ON ai_files(session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_files_status ON ai_files(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_file_chunks_file_id ON ai_file_chunks(file_id)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_file_chunks_metadata ON ai_file_chunks USING GIN(metadata)"
            )
            self._relax_embedding_column_if_needed(cur)
            conn.commit()

    @staticmethod
    def _relax_embedding_column_if_needed(cur: psycopg.Cursor) -> None:
        """Keep embedding column dimension-flexible for demo speed.

        If the column was created earlier as `vector(1024)` and we switch to a
        different embedding model (e.g. 4096-dim), inserts will fail.
        We relax it to plain `vector` once, so future model swaps are painless.
        """
        cur.execute(
            """
            SELECT format_type(a.atttypid, a.atttypmod) AS embedding_type
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'ai_file_chunks'
              AND n.nspname = current_schema()
              AND a.attname = 'embedding'
              AND a.attnum > 0
              AND NOT a.attisdropped
            """
        )
        row = cur.fetchone()
        if not row:
            return

        embedding_type = str(row["embedding_type"] or "").lower()
        if embedding_type.startswith("vector("):
            logger.info(
                "rag.schema.adjust embedding column type %s -> vector",
                embedding_type,
            )
            try:
                cur.execute(
                    """
                    ALTER TABLE ai_file_chunks
                    ALTER COLUMN embedding TYPE vector
                    USING embedding::vector
                    """
                )
            except psycopg.Error as exc:
                logger.warning(
                    "rag.schema.adjust.failed first_try=%s, dropping vector indexes then retry",
                    exc,
                )
                cur.execute(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = current_schema()
                      AND tablename = 'ai_file_chunks'
                      AND (
                        indexdef ILIKE '%% USING ivfflat %%'
                        OR indexdef ILIKE '%% USING hnsw %%'
                      )
                    """
                )
                for index_row in cur.fetchall():
                    index_name = index_row["indexname"]
                    logger.info("rag.schema.adjust.drop_index index=%s", index_name)
                    cur.execute(f'DROP INDEX IF EXISTS "{index_name}"')

                cur.execute(
                    """
                    ALTER TABLE ai_file_chunks
                    ALTER COLUMN embedding TYPE vector
                    USING embedding::vector
                    """
                )

    async def save_text_file(
        self,
        *,
        file_bytes: bytes,
        original_name: str,
        session_id: str | None,
        mime_type: str | None,
    ) -> UploadResult:
        file_id = str(uuid.uuid4())
        safe_name = self._safe_filename(original_name)
        saved_name = f"{uuid.uuid4().hex}_{safe_name}"
        absolute_path = self.upload_dir / saved_name
        relative_path = f"doc/{saved_name}"
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        absolute_path.write_bytes(file_bytes)
        text = self._decode_text(file_bytes)

        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_files (
                    id, session_id, original_name, saved_name, local_path,
                    mime_type, size_bytes, sha256, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PROCESSING')
                """,
                (
                    file_id,
                    session_id,
                    original_name,
                    saved_name,
                    relative_path,
                    mime_type,
                    len(file_bytes),
                    sha256,
                ),
            )
            conn.commit()

        try:
            chunks = self._chunk_text(text)
            for idx, chunk in enumerate(chunks, start=1):
                embedding = await self.embed_text(chunk)
                metadata = {
                    "original_name": original_name,
                    "saved_name": saved_name,
                    "chunk_no": idx,
                    "session_id": session_id,
                }
                vector_literal = self._vector_literal(embedding)
                with self._connect() as conn, conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO ai_file_chunks (
                            file_id, chunk_no, content, token_count, metadata, embedding
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector)
                        """,
                        (
                            file_id,
                            idx,
                            chunk,
                            max(1, len(chunk) // 4),
                            json.dumps(metadata, ensure_ascii=False),
                            vector_literal,
                        ),
                    )
                    conn.commit()

            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ai_files
                    SET status = 'READY', error_message = NULL, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (file_id,),
                )
                conn.commit()
            return UploadResult(
                file_id=file_id,
                original_name=original_name,
                local_path=relative_path,
                status="READY",
                chunk_count=len(chunks),
            )
        except Exception as exc:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ai_files
                    SET status = 'FAILED', error_message = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (str(exc), file_id),
                )
                conn.commit()
            logger.exception("rag.upload.failed file=%s", original_name)
            raise

    async def search(
        self,
        *,
        query: str,
        session_id: str | None,
        top_k: int = 4,
    ) -> tuple[list[RetrievedChunk], SearchMetrics]:
        if not query.strip():
            return [], SearchMetrics(
                top_k_requested=max(1, min(top_k, 8)),
                top_k_returned=0,
                fill_rate_at_k=0.0,
                corpus_chunk_count=0,
                corpus_file_count=0,
                hit_file_count=0,
                recall_proxy_at_k=0.0,
                score_min=0.0,
                score_max=0.0,
                score_avg=0.0,
                latency_ms=0,
            )

        started_at = time.perf_counter()
        query_embedding = await self.embed_text(query)
        query_vector = self._vector_literal(query_embedding)
        limit = max(1, min(top_k, 8))

        corpus_sql = """
            SELECT
                COUNT(*) AS chunk_count,
                COUNT(DISTINCT c.file_id) AS file_count
            FROM ai_file_chunks c
            JOIN ai_files f ON f.id = c.file_id
            WHERE f.status = 'READY'
              AND (%s::text IS NULL OR f.session_id = %s::text)
        """
        sql = """
            SELECT
                c.content AS content,
                f.original_name AS file_name,
                c.file_id AS file_id,
                c.chunk_no AS chunk_no,
                (1 - (c.embedding <=> %s::vector)) AS score
            FROM ai_file_chunks c
            JOIN ai_files f ON f.id = c.file_id
            WHERE f.status = 'READY'
              AND (%s::text IS NULL OR f.session_id = %s::text)
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(corpus_sql, (session_id, session_id))
            corpus_row = cur.fetchone() or {"chunk_count": 0, "file_count": 0}
            cur.execute(sql, (query_vector, session_id, session_id, query_vector, limit))
            rows = cur.fetchall()

        result: list[RetrievedChunk] = []
        hit_file_ids: set[str] = set()
        score_values: list[float] = []
        for row in rows:
            score = float(row["score"] or 0.0)
            score_values.append(score)
            hit_file_ids.add(str(row["file_id"]))
            result.append(
                RetrievedChunk(
                    content=row["content"],
                    score=score,
                    file_name=row["file_name"],
                    chunk_no=int(row["chunk_no"]),
                )
            )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        corpus_file_count = int(corpus_row["file_count"] or 0)
        top_k_returned = len(result)
        score_min = min(score_values) if score_values else 0.0
        score_max = max(score_values) if score_values else 0.0
        score_avg = sum(score_values) / len(score_values) if score_values else 0.0
        metrics = SearchMetrics(
            top_k_requested=limit,
            top_k_returned=top_k_returned,
            fill_rate_at_k=top_k_returned / limit if limit else 0.0,
            corpus_chunk_count=int(corpus_row["chunk_count"] or 0),
            corpus_file_count=corpus_file_count,
            hit_file_count=len(hit_file_ids),
            # Strict recall needs labeled ground truth; for demo we output a recall proxy:
            # hit files / candidate files in this session scope.
            recall_proxy_at_k=(len(hit_file_ids) / corpus_file_count) if corpus_file_count else 0.0,
            score_min=score_min,
            score_max=score_max,
            score_avg=score_avg,
            latency_ms=latency_ms,
        )
        logger.info(
            "rag.search.metrics session_id=%s top_k=%s returned=%s fill=%.3f "
            "corpus_chunks=%s corpus_files=%s hit_files=%s recall_proxy=%.3f "
            "score_min=%.3f score_avg=%.3f score_max=%.3f latency_ms=%s",
            session_id or "(none)",
            metrics.top_k_requested,
            metrics.top_k_returned,
            metrics.fill_rate_at_k,
            metrics.corpus_chunk_count,
            metrics.corpus_file_count,
            metrics.hit_file_count,
            metrics.recall_proxy_at_k,
            metrics.score_min,
            metrics.score_avg,
            metrics.score_max,
            metrics.latency_ms,
        )
        return result, metrics

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return ""
        lines = [
            "以下是用户上传文档中与当前问题最相关的片段，请优先基于这些内容回答："
        ]
        for item in chunks:
            cleaned = _WHITESPACE.sub(" ", item.content).strip()
            preview = cleaned[:320] + ("..." if len(cleaned) > 320 else "")
            lines.append(
                f"- 来源: {item.file_name} (chunk {item.chunk_no}, score={item.score:.3f})\n  内容: {preview}"
            )
        return "\n".join(lines)

    async def embed_text(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ValueError("文本为空，无法生成向量")

        embed_url = self._embed_url()
        payload = {"model": self.embedding_model, "input": [normalized]}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(embed_url, json=payload)
            if response.status_code == 404:
                fallback_url = self._embeddings_url()
                fallback_payload = {"model": self.embedding_model, "prompt": normalized}
                response = await client.post(fallback_url, json=fallback_payload)

            response.raise_for_status()
            data = response.json()

        if isinstance(data.get("embeddings"), list):
            embeddings = data["embeddings"]
            if embeddings and isinstance(embeddings[0], list):
                return [float(value) for value in embeddings[0]]
        if isinstance(data.get("embedding"), list):
            return [float(value) for value in data["embedding"]]
        raise RuntimeError(f"Ollama embedding response format not recognized: {data}")

    def _embed_url(self) -> str:
        if self.ollama_base_url.endswith("/api"):
            return f"{self.ollama_base_url}/embed"
        return f"{self.ollama_base_url}/api/embed"

    def _embeddings_url(self) -> str:
        if self.ollama_base_url.endswith("/api"):
            return f"{self.ollama_base_url}/embeddings"
        return f"{self.ollama_base_url}/api/embeddings"

    @staticmethod
    def _safe_filename(filename: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
        return normalized or "uploaded.txt"

    @staticmethod
    def _decode_text(file_bytes: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = file_bytes.decode("utf-8", errors="ignore")

        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            raise ValueError("上传文件为空或无法解析为文本")
        return text

    @staticmethod
    def _chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
        cleaned = _WHITESPACE.sub(" ", text).strip()
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

    @staticmethod
    def _vector_literal(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
