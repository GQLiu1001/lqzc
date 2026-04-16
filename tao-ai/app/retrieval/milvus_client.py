"""Milvus 连接管理。

提供全局连接 (pymilvus connections + utility_name alias)。
use_stub_stores=True 时不初始化。
"""
from __future__ import annotations

import logging

from pymilvus import MilvusClient, connections

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: MilvusClient | None = None
_ALIAS = "tao_ai"


def get_milvus_client() -> MilvusClient:
    global _client
    if _client is not None:
        return _client
    s = get_settings()
    uri = f"http://{s.milvus_host}:{s.milvus_port}"
    _client = MilvusClient(uri=uri)
    logger.info("Milvus client created uri=%s", uri)
    return _client


def connect_milvus() -> None:
    s = get_settings()
    connections.connect(
        alias=_ALIAS,
        host=s.milvus_host,
        port=s.milvus_port,
    )
    logger.info("Milvus connected alias=%s host=%s:%d", _ALIAS, s.milvus_host, s.milvus_port)


def disconnect_milvus() -> None:
    global _client
    try:
        connections.disconnect(alias=_ALIAS)
    except Exception:
        pass
    if _client is not None:
        _client.close()
        _client = None
    logger.info("Milvus disconnected")
