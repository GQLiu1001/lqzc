"""Milvus 连接管理。

支持两种部署形态:
  1. Milvus Lite  — settings.milvus_uri = "./data/milvus.db" (本地文件, 无需 Docker)
  2. Milvus Server — settings.milvus_uri = "http://host:19530" 或留空走 host:port 字段

use_real_milvus=False 且 use_stub_stores=True 时不初始化连接。
"""
from __future__ import annotations

import logging

from pymilvus import MilvusClient

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: MilvusClient | None = None


def _resolve_uri() -> str:
    s = get_settings()
    if s.milvus_uri:
        return s.milvus_uri
    return f"http://{s.milvus_host}:{s.milvus_port}"


def get_milvus_client() -> MilvusClient:
    global _client
    if _client is not None:
        return _client
    uri = _resolve_uri()
    _client = MilvusClient(uri=uri)
    logger.info("Milvus client created uri=%s", uri)
    return _client


def disconnect_milvus() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
    logger.info("Milvus disconnected")
