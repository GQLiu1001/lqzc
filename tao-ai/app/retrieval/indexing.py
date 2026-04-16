"""文档切分 + 向量化 + 入库 Milvus。

支持两种入库方式:
  1. seed_index(): 将内置种子文档写入 (M3 冒烟)
  2. index_documents(): 外部文档批量入库 (供 /files 接口调用)
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.models.factory import make_embeddings
from app.retrieval.collections import get_source_collection_map
from app.retrieval.milvus_client import get_milvus_client

logger = logging.getLogger(__name__)

SEED_DOCS: list[dict[str, str]] = [
    {
        "doc_id": "faq-ship-001",
        "source": "customer_faq",
        "text": "订单正常在 24 小时内安排发货,遇大促或节假日顺延,可在订单详情查看实时物流。",
    },
    {
        "doc_id": "faq-refund-001",
        "source": "customer_policy",
        "text": "未发货订单支持 24 小时内全额退款,已发货订单需签收后发起售后,7 天无理由退款。",
    },
    {
        "doc_id": "faq-coupon-001",
        "source": "customer_policy",
        "text": "优惠券不支持叠加使用,过期券不再补发;因平台故障作废的券可联系客服提交补发申请。",
    },
    {
        "doc_id": "faq-refund-002",
        "source": "customer_policy",
        "text": "退款金额原路返回至支付账户,微信支付 1-3 个工作日到账,银行卡 3-7 个工作日到账。",
    },
    {
        "doc_id": "faq-ship-002",
        "source": "customer_faq",
        "text": "如需修改收货地址,请在发货前联系客服修改;已发货订单不支持修改地址,可拒收后重新下单。",
    },
    {
        "doc_id": "faq-coupon-002",
        "source": "customer_policy",
        "text": "新用户首单立减 10 元,优惠券有效期 7 天,每个账号限领一次,不可转赠。",
    },
    {
        "doc_id": "wh-sop-001",
        "source": "warehouse_sop",
        "text": "仓库出库量以 ERP T+1 结算数据为准,近 7 天数据可通过 inventory.metric 工具查询。",
    },
    {
        "doc_id": "wh-sop-002",
        "source": "warehouse_sop",
        "text": "A 仓负责华东区域发货,B 仓负责华南区域;SKU 库存不足时自动触发跨仓调拨。",
    },
]


def index_documents(docs: list[dict[str, Any]]) -> int:
    """将文档批量入库 Milvus。

    每条 doc 需包含 doc_id, text, source 字段。
    返回成功入库条数。
    """
    if not docs:
        return 0

    client = get_milvus_client()
    embedder = make_embeddings()
    source_map = get_source_collection_map()
    count = 0

    by_source: dict[str, list[dict]] = {}
    for doc in docs:
        src = doc.get("source", "customer_faq")
        by_source.setdefault(src, []).append(doc)

    for source, group in by_source.items():
        collection = source_map.get(source)
        if not collection:
            logger.warning("indexing: unknown source=%s, skip %d docs", source, len(group))
            continue

        texts = [d["text"] for d in group]
        vectors = embedder.embed_documents(texts)

        data = [
            {
                "doc_id": d["doc_id"],
                "text": d["text"],
                "source": d["source"],
                "embedding": vec,
            }
            for d, vec in zip(group, vectors)
        ]

        client.upsert(collection_name=collection, data=data)
        count += len(data)
        logger.info("indexing: upserted %d docs into %s", len(data), collection)

    return count


def seed_index() -> int:
    """将内置种子文档写入 Milvus (M3 冒烟用)。"""
    logger.info("seed_index: indexing %d seed docs", len(SEED_DOCS))
    return index_documents(SEED_DOCS)


def collection_stats() -> dict[str, int]:
    """返回每个 collection 的文档数。"""
    client = get_milvus_client()
    source_map = get_source_collection_map()
    stats = {}
    for source, collection in source_map.items():
        try:
            info = client.get_collection_stats(collection)
            stats[source] = info.get("row_count", 0)
        except Exception:
            stats[source] = -1
    return stats
