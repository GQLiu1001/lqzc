"""提供与milvus客户端相关的实现。"""

from __future__ import annotations

import logging
from typing import Any

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.config import settings


logger = logging.getLogger(__name__)


class MilvusClient:
    """Milvus 向量库客户端封装。

    它解决的是“怎么和 Milvus 打交道”这个底层问题：
    - 连接
    - 建 collection
    - 搜索
    - 插入向量

    上层检索逻辑不需要关心 pymilvus 的细节，统一走这里。
    """
    def __init__(self) -> None:
        """在启动时尝试连接 Milvus。"""
        self.alias = "tao_runtime"
        self.connected = False
        try:
            connections.connect(
                alias=self.alias,
                host=settings.milvus_host,
                port=settings.milvus_port,
                db_name=settings.milvus_db,
            )
            self.connected = True
        except Exception:
            self.connected = False

    def ensure_collection(self, name: str, *, dim: int) -> None:
        """确保目标 collection 存在，且向量维度正确。

        这里有个很重要的防御性逻辑：
        如果 collection 已存在，但 embedding 维度和当前模型不一致，
        会直接删掉重建。否则后续插入或搜索很容易报错。
        """
        if not self.connected:
            return
        if utility.has_collection(name, using=self.alias):
            existing_dim = self._current_embedding_dim(name)
            if existing_dim == dim:
                return
            if existing_dim is not None:
                # 模型换过 embedding 维度时，旧 collection 需要重建，否则数据结构不兼容。
                logger.warning(
                    "milvus embedding dim mismatch for %s: existing=%s expected=%s, recreating collection",
                    name,
                    existing_dim,
                    dim,
                )
                utility.drop_collection(name, using=self.alias)

        # 这里定义的是一条知识片段在向量库中的结构。
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields=fields, description=f"{name} knowledge collection")
        collection = Collection(name=name, schema=schema, using=self.alias)
        collection.create_index(
            field_name="embedding",
            index_params={"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 1024}},
        )
        collection.load()

    def _current_embedding_dim(self, collection_name: str) -> int | None:
        """读取现有 collection 的 embedding 维度。"""
        try:
            collection = Collection(collection_name, using=self.alias)
            for field in collection.schema.fields:
                if field.name == "embedding" and field.dtype == DataType.FLOAT_VECTOR:
                    raw_dim = (field.params or {}).get("dim")
                    if raw_dim is None:
                        return None
                    return int(raw_dim)
        except Exception:
            return None
        return None

    def search(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        top_k: int,
        expr: str | None = None,
    ) -> list[dict[str, Any]]:
        """执行向量搜索并整理结果。

        `expr` 是元数据过滤条件，比如按租户筛数据；
        `output_fields` 决定了除相似度分数外，还要把哪些字段一起取出来。
        """
        if not self.connected or not utility.has_collection(collection_name, using=self.alias):
            return []

        collection = Collection(collection_name, using=self.alias)
        collection.load()
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=max(1, min(top_k, 10)),
            expr=expr,
            output_fields=["content", "source", "metadata"],
        )

        # pymilvus 返回的是底层对象，这里统一转换成项目内部更好用的 dict 结构。
        hits: list[dict[str, Any]] = []
        for row in results[0]:
            entity = row.entity
            hits.append(
                {
                    "content": entity.get("content", ""),
                    "source": entity.get("source", collection_name),
                    "metadata": entity.get("metadata", {}) or {},
                    "score": float(row.score),
                }
            )
        return hits

    def insert_chunks(self, *, collection_name: str, rows: list[dict[str, Any]], dim: int) -> int:
        """把切好的文本块批量写入向量库。

        每一行通常对应一个知识片段，包含：
        - 文本内容
        - 来源文件
        - 元数据
        - embedding 向量
        """
        if not self.connected or not rows:
            return 0

        self.ensure_collection(collection_name, dim=dim)
        collection = Collection(collection_name, using=self.alias)
        content_list: list[str] = []
        source_list: list[str] = []
        metadata_list: list[dict[str, Any]] = []
        embedding_list: list[list[float]] = []

        # Milvus 批量插入需要按“列”组织数据，所以这里先把每个字段拆成独立列表。
        for row in rows:
            content_list.append(str(row.get("content", "")))
            source_list.append(str(row.get("source", collection_name)))
            metadata_list.append(row.get("metadata", {}) or {})
            embedding_list.append([float(item) for item in row.get("embedding", [])])

        if not embedding_list:
            return 0
        # 再次做维度校验，避免脏数据写进向量库。
        if any(len(vector) != dim for vector in embedding_list):
            raise ValueError(
                f"embedding dimension mismatch before insert: expected={dim}, "
                f"got={sorted({len(vector) for vector in embedding_list})}"
            )

        collection.insert([content_list, source_list, metadata_list, embedding_list])
        collection.flush()
        return len(rows)

    def ping(self) -> tuple[bool, str | None]:
        """检查 Milvus 当前是否可用。"""
        if not self.connected:
            return False, "milvus not connected"
        try:
            utility.list_collections(using=self.alias)
            return True, None
        except Exception as exc:
            return False, str(exc)
