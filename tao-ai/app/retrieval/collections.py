"""多域 Milvus Collection Schema + 自动建表。

三个 collection:
  - customer_faq_collection     客服 FAQ
  - customer_policy_collection  客服政策
  - warehouse_sop_collection    仓储 SOP

每个 collection 统一字段:
  doc_id (VARCHAR PK) | text (VARCHAR) | source (VARCHAR) | embedding (FLOAT_VECTOR)
"""
from __future__ import annotations

import logging

from pymilvus import CollectionSchema, DataType, FieldSchema

from app.config import get_settings
from app.retrieval.milvus_client import get_milvus_client

logger = logging.getLogger(__name__)


def _build_schema(dim: int) -> CollectionSchema:
    fields = [
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    return CollectionSchema(fields=fields, enable_dynamic_field=False)


def _index_params() -> dict:
    return {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }


def ensure_collections() -> list[str]:
    """确保三个 collection 存在, 不存在则建。返回 collection name 列表。"""
    s = get_settings()
    client = get_milvus_client()
    dim = s.milvus_embedding_dim
    names = [
        s.milvus_customer_faq_collection,
        s.milvus_customer_policy_collection,
        s.milvus_warehouse_sop_collection,
    ]

    schema = _build_schema(dim)

    for name in names:
        if client.has_collection(name):
            logger.info("collection %s already exists", name)
            continue
        client.create_collection(
            collection_name=name,
            schema=schema,
        )
        client.create_index(
            collection_name=name,
            field_name="embedding",
            index_params=_index_params(),
        )
        logger.info("collection %s created with dim=%d", name, dim)

    return names


SOURCE_TO_COLLECTION: dict[str, str] = {}


def get_source_collection_map() -> dict[str, str]:
    """返回 source → collection_name 映射。"""
    global SOURCE_TO_COLLECTION
    if SOURCE_TO_COLLECTION:
        return SOURCE_TO_COLLECTION
    s = get_settings()
    SOURCE_TO_COLLECTION = {
        "customer_faq": s.milvus_customer_faq_collection,
        "customer_policy": s.milvus_customer_policy_collection,
        "warehouse_sop": s.milvus_warehouse_sop_collection,
    }
    return SOURCE_TO_COLLECTION
