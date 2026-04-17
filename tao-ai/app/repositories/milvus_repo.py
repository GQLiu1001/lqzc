from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_ollama import OllamaEmbeddings
from pymilvus import DataType, MilvusClient

from app.core.config import settings
from app.rag.constants import CACHE_ROOT, PUBLIC_ACCESS
from app.schemas.rag import RetrievedChunk

logger = logging.getLogger(__name__)

COLLECTION_NAME = settings.rag_collection_name
PRIMARY_FIELD = "chunk_id"
VECTOR_FIELD = "embedding"
SYNC_STATE_PATH = CACHE_ROOT / "milvus_sync.json"

MAX_ID_BYTES = 256
MAX_TITLE_BYTES = 512
MAX_CONTENT_BYTES = 16384
MAX_DOMAIN_BYTES = 32
MAX_SCENE_BYTES = 64
MAX_SOURCE_TYPE_BYTES = 64
MAX_VERSION_BYTES = 64
MAX_ACCESS_LEVEL_BYTES = 32
MAX_TENANT_BYTES = 128
MAX_ARRAY_VALUE_BYTES = 64
ROLE_ALLOWLIST_CAPACITY = 16
WAREHOUSE_SCOPE_CAPACITY = 32
UPSERT_BATCH_SIZE = 32


class MilvusRepository:

    def __init__(self) -> None:
        self._client: MilvusClient | None = None
        self._embeddings: OllamaEmbeddings | None = None
        self._embedding_dim: int | None = None
        self._availability_checked = False
        self._available = False
        self._reason = "not_checked"
        self._indexed_signature: str | None = None
        self._indexed_model: str | None = None
        self._load_sync_state()

    def availability(self, refresh: bool = False) -> tuple[bool, str]:
        if self._availability_checked and not refresh:
            return self._available, self._reason

        self._availability_checked = True

        if not settings.rag_enable_milvus:
            self._available = False
            self._reason = "disabled_by_config"
            return self._available, self._reason

        try:
            client = self._get_client()
            client.list_collections(timeout=3)
            self._available = True
            self._reason = "ok"
        except Exception as exc:
            logger.warning("Milvus unavailable, fallback to local retrieval: %s", exc)
            self._available = False
            self._reason = str(exc)
            self._client = None

        return self._available, self._reason

    async def search(
        self,
        query: str,
        top_k: int,
        filters: dict,
    ) -> list[RetrievedChunk]:
        return await asyncio.to_thread(self._search_sync, query, top_k, filters)

    async def index_chunks(self, chunks: list[dict], force_refresh: bool = False) -> dict:
        return await asyncio.to_thread(self._index_chunks_sync, chunks, force_refresh)

    def _search_sync(self, query: str, top_k: int, filters: dict) -> list[RetrievedChunk]:
        available, _ = self.availability(refresh=True)
        if not available:
            return []

        if not self._has_collection():
            return []

        try:
            client = self._get_client()
            client.load_collection(COLLECTION_NAME, timeout=10)
            query_vector = self._get_embeddings().embed_query(query)
            expr = self._build_filter_expression(filters)
            dense_limit = max(top_k, min(settings.rag_recall_k, 32))
            raw_results = client.search(
                collection_name=COLLECTION_NAME,
                data=[query_vector],
                anns_field=VECTOR_FIELD,
                limit=dense_limit,
                filter=expr,
                output_fields=[
                    "doc_id",
                    "title",
                    "content",
                    "domain",
                    "scene",
                    "source_type",
                    "version",
                    "effective_at_ts",
                    "metadata",
                    "role_allowlist",
                    "warehouse_scope",
                ],
                search_params={"metric_type": "COSINE", "params": {}},
                timeout=10,
            )
        except Exception as exc:
            logger.warning("Milvus dense retrieval failed: %s", exc)
            return []

        if not raw_results:
            return []

        hits: list[RetrievedChunk] = []
        for hit in raw_results[0]:
            metadata = dict(hit.get("metadata") or {})
            metadata.setdefault("role_allowlist", list(hit.get("role_allowlist") or []))
            metadata.setdefault("warehouse_scope", list(hit.get("warehouse_scope") or []))

            raw_score = float(hit.get("distance") or 0.0)
            hits.append(
                RetrievedChunk(
                    doc_id=hit.get("doc_id") or "",
                    chunk_id=hit.get(PRIMARY_FIELD) or "",
                    title=hit.get("title") or "",
                    content=hit.get("content") or "",
                    score=round(max(0.0, min(raw_score, 1.0)), 6),
                    domain=hit.get("domain") or "",
                    scene=hit.get("scene") or "general",
                    source_type=hit.get("source_type") or "",
                    version=hit.get("version") or None,
                    effective_at=_timestamp_to_datetime(hit.get("effective_at_ts")),
                    metadata=metadata,
                )
            )
        return hits

    def _index_chunks_sync(self, chunks: list[dict], force_refresh: bool) -> dict:
        available, reason = self.availability(refresh=True)
        if not available:
            return {"available": False, "indexed": 0, "message": reason}

        if not chunks:
            return {"available": True, "indexed": 0, "message": "no chunks to index"}

        signature = self._build_signature(chunks)
        if not force_refresh and self._is_collection_current(signature):
            return {
                "available": True,
                "indexed": 0,
                "message": "Milvus index already up to date",
                "syncSkipped": True,
            }

        try:
            embedding_dim = self._embedding_dimension()
            self._rebuild_collection(embedding_dim)
            indexed_count = 0

            for batch in _batch(chunks, UPSERT_BATCH_SIZE):
                texts = [str(item.get("content") or "") for item in batch]
                vectors = self._get_embeddings().embed_documents(texts)
                records = [
                    self._build_record(chunk=item, vector=vector)
                    for item, vector in zip(batch, vectors, strict=True)
                ]
                result = self._get_client().upsert(
                    collection_name=COLLECTION_NAME,
                    data=records,
                    timeout=20,
                )
                indexed_count += int(result.get("upsert_count") or len(records))

            self._get_client().load_collection(COLLECTION_NAME, timeout=10)
            self._indexed_signature = signature
            self._indexed_model = settings.ollama_embed_model
            self._save_sync_state(signature, indexed_count)
            return {
                "available": True,
                "indexed": indexed_count,
                "message": "Milvus index rebuilt",
                "syncSkipped": False,
            }
        except Exception as exc:
            logger.exception("Milvus indexing failed")
            return {
                "available": True,
                "indexed": 0,
                "message": f"Milvus indexing failed: {exc}",
                "syncSkipped": False,
            }

    def _get_client(self) -> MilvusClient:
        if self._client is None:
            uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
            self._client = MilvusClient(
                uri=uri,
                db_name=settings.milvus_db,
                timeout=3,
            )
        return self._client

    def _get_embeddings(self) -> OllamaEmbeddings:
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                model=settings.ollama_embed_model,
                base_url=settings.ollama_base_url,
            )
        return self._embeddings

    def _embedding_dimension(self) -> int:
        if self._embedding_dim is None:
            probe = self._get_embeddings().embed_query("taoai rag dimension probe")
            self._embedding_dim = len(probe)
        return self._embedding_dim

    def _has_collection(self) -> bool:
        try:
            return bool(self._get_client().has_collection(COLLECTION_NAME, timeout=5))
        except Exception:
            return False

    def _rebuild_collection(self, embedding_dim: int) -> None:
        client = self._get_client()
        if self._has_collection():
            client.drop_collection(COLLECTION_NAME, timeout=10)

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name=PRIMARY_FIELD, datatype=DataType.VARCHAR, is_primary=True, max_length=MAX_ID_BYTES)
        schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR, max_length=MAX_ID_BYTES)
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=MAX_TITLE_BYTES)
        schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=MAX_CONTENT_BYTES)
        schema.add_field(field_name="domain", datatype=DataType.VARCHAR, max_length=MAX_DOMAIN_BYTES)
        schema.add_field(field_name="scene", datatype=DataType.VARCHAR, max_length=MAX_SCENE_BYTES)
        schema.add_field(field_name="source_type", datatype=DataType.VARCHAR, max_length=MAX_SOURCE_TYPE_BYTES)
        schema.add_field(field_name="version", datatype=DataType.VARCHAR, max_length=MAX_VERSION_BYTES)
        schema.add_field(field_name="effective_at_ts", datatype=DataType.INT64)
        schema.add_field(field_name="access_level", datatype=DataType.VARCHAR, max_length=MAX_ACCESS_LEVEL_BYTES)
        schema.add_field(field_name="tenant_id", datatype=DataType.VARCHAR, max_length=MAX_TENANT_BYTES)
        schema.add_field(field_name="is_active", datatype=DataType.BOOL)
        schema.add_field(
            field_name="role_allowlist",
            datatype=DataType.ARRAY,
            element_type=DataType.VARCHAR,
            max_capacity=ROLE_ALLOWLIST_CAPACITY,
            max_length=MAX_ARRAY_VALUE_BYTES,
        )
        schema.add_field(
            field_name="warehouse_scope",
            datatype=DataType.ARRAY,
            element_type=DataType.VARCHAR,
            max_capacity=WAREHOUSE_SCOPE_CAPACITY,
            max_length=MAX_ARRAY_VALUE_BYTES,
        )
        schema.add_field(field_name="metadata", datatype=DataType.JSON)
        schema.add_field(field_name=VECTOR_FIELD, datatype=DataType.FLOAT_VECTOR, dim=embedding_dim)

        index_params = client.prepare_index_params()
        index_params.add_index(field_name=VECTOR_FIELD, index_type="AUTOINDEX", metric_type="COSINE")

        client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema,
            index_params=index_params,
            consistency_level="Bounded",
        )

    def _build_record(self, chunk: dict, vector: list[float]) -> dict:
        metadata = dict(chunk.get("metadata") or {})
        role_allowlist = _normalize_array(metadata.get("role_allowlist"), ROLE_ALLOWLIST_CAPACITY)
        warehouse_scope = _normalize_array(metadata.get("warehouse_scope"), WAREHOUSE_SCOPE_CAPACITY)
        access_level = _truncate_text(metadata.get("access_level") or PUBLIC_ACCESS, MAX_ACCESS_LEVEL_BYTES)
        tenant_id = _truncate_text(metadata.get("tenant_id") or "", MAX_TENANT_BYTES)
        is_active = metadata.get("is_active", True) is not False

        normalized_metadata = {
            **metadata,
            "access_level": access_level,
            "tenant_id": tenant_id,
            "role_allowlist": role_allowlist,
            "warehouse_scope": warehouse_scope,
            "is_active": is_active,
        }

        return {
            PRIMARY_FIELD: _truncate_text(chunk.get(PRIMARY_FIELD) or "", MAX_ID_BYTES),
            "doc_id": _truncate_text(chunk.get("doc_id") or "", MAX_ID_BYTES),
            "title": _truncate_text(chunk.get("title") or "", MAX_TITLE_BYTES),
            "content": _truncate_text(chunk.get("content") or "", MAX_CONTENT_BYTES),
            "domain": _truncate_text(chunk.get("domain") or "", MAX_DOMAIN_BYTES),
            "scene": _truncate_text(chunk.get("scene") or "general", MAX_SCENE_BYTES),
            "source_type": _truncate_text(chunk.get("source_type") or "", MAX_SOURCE_TYPE_BYTES),
            "version": _truncate_text(chunk.get("version") or "", MAX_VERSION_BYTES),
            "effective_at_ts": _iso_to_timestamp(chunk.get("effective_at")),
            "access_level": access_level,
            "tenant_id": tenant_id,
            "is_active": is_active,
            "role_allowlist": role_allowlist,
            "warehouse_scope": warehouse_scope,
            "metadata": normalized_metadata,
            VECTOR_FIELD: vector,
        }

    def _is_collection_current(self, signature: str) -> bool:
        return (
            signature == self._indexed_signature
            and self._indexed_model == settings.ollama_embed_model
            and self._has_collection()
        )

    def _build_filter_expression(self, filters: dict) -> str:
        clauses = [
            f'domain == {json.dumps(filters.get("domain", ""), ensure_ascii=False)}',
            "is_active == true",
            f"effective_at_ts <= {int(datetime.now(timezone.utc).timestamp())}",
        ]

        scene = filters.get("scene")
        scene_allowlist = [value for value in filters.get("scene_allowlist", []) if value]
        if scene and scene != "general":
            clauses.append(_any_equals("scene", [scene, "general", *scene_allowlist]))

        user_type = filters.get("user_type") or "customer"
        if user_type != "staff":
            clauses.append('access_level != "staff"')

        role = filters.get("role")
        if role:
            clauses.append(f'(ARRAY_LENGTH(role_allowlist) == 0 or ARRAY_CONTAINS(role_allowlist, {json.dumps(role, ensure_ascii=False)}))')
        else:
            clauses.append("ARRAY_LENGTH(role_allowlist) == 0")

        tenant_id = filters.get("tenant_id")
        if tenant_id:
            encoded = json.dumps(str(tenant_id), ensure_ascii=False)
            clauses.append(f'(tenant_id == "" or tenant_id == {encoded})')

        warehouse_scope = [str(value) for value in (filters.get("warehouse_scope") or []) if value]
        if warehouse_scope:
            clauses.append(
                f"(ARRAY_LENGTH(warehouse_scope) == 0 or ARRAY_CONTAINS_ANY(warehouse_scope, {json.dumps(warehouse_scope, ensure_ascii=False)}))"
            )

        supported_fields = {
            PRIMARY_FIELD,
            "doc_id",
            "domain",
            "scene",
            "source_type",
            "version",
            "access_level",
            "tenant_id",
            "is_active",
        }
        for key, expected in filters.items():
            if key in {"domain", "scene", "scene_allowlist", "user_type", "role", "tenant_id", "warehouse_scope"}:
                continue
            if expected is None or key not in supported_fields:
                continue
            if isinstance(expected, list):
                if expected:
                    clauses.append(_any_equals(key, expected))
                continue
            clauses.append(f"{key} == {json.dumps(expected, ensure_ascii=False)}")

        return " and ".join(clause for clause in clauses if clause)

    def _build_signature(self, chunks: list[dict]) -> str:
        digest_source = [
            {
                "chunk_id": chunk.get("chunk_id"),
                "checksum": (chunk.get("metadata") or {}).get("checksum"),
                "version": chunk.get("version"),
            }
            for chunk in chunks
        ]
        payload = {
            "embed_model": settings.ollama_embed_model,
            "collection": COLLECTION_NAME,
            "chunks": digest_source,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha1(raw).hexdigest()

    def _load_sync_state(self) -> None:
        if not SYNC_STATE_PATH.exists():
            return
        try:
            payload = json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to load Milvus sync state from %s", SYNC_STATE_PATH)
            return

        if payload.get("collection") != COLLECTION_NAME:
            return
        self._indexed_signature = payload.get("signature")
        self._indexed_model = payload.get("embedModel")

    def _save_sync_state(self, signature: str, chunk_count: int) -> None:
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        payload = {
            "collection": COLLECTION_NAME,
            "signature": signature,
            "embedModel": settings.ollama_embed_model,
            "chunkCount": chunk_count,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        SYNC_STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _any_equals(field: str, values: list[Any]) -> str:
    normalized = [value for value in values if value not in (None, "")]
    if not normalized:
        return ""
    unique_values = list(dict.fromkeys(normalized))
    return "(" + " or ".join(f"{field} == {json.dumps(value, ensure_ascii=False)}" for value in unique_values) + ")"


def _truncate_text(value: Any, max_bytes: int) -> str:
    text = str(value or "")
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", errors="ignore")


def _normalize_array(value: Any, max_capacity: int) -> list[str]:
    if not value:
        return []
    if isinstance(value, (str, bytes)):
        values = [value]
    else:
        values = list(value)
    normalized = [_truncate_text(item, MAX_ARRAY_VALUE_BYTES) for item in values if item not in (None, "")]
    return normalized[:max_capacity]


def _iso_to_timestamp(value: Any) -> int:
    if not value:
        return 0
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _timestamp_to_datetime(value: Any) -> datetime | None:
    try:
        timestamp = int(value or 0)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _batch(items: list[dict], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


_repo = MilvusRepository()


def get_milvus_repository() -> MilvusRepository:
    return _repo
