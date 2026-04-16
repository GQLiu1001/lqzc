"""Checkpointer 工厂。

M1: InMemorySaver (进程内)
M2: AIOMySQLSaver (langgraph-checkpoint-mysql 官方包)
"""
from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from app.config import get_settings

logger = logging.getLogger(__name__)

_mysql_saver = None


@lru_cache(maxsize=1)
def get_checkpointer() -> BaseCheckpointSaver:
    s = get_settings()
    if s.use_stub_stores:
        return InMemorySaver()
    return _get_mysql_checkpointer()


def _get_mysql_checkpointer() -> BaseCheckpointSaver:
    global _mysql_saver
    if _mysql_saver is not None:
        return _mysql_saver
    from langgraph.checkpoint.mysql.aio import AIOMySQLSaver

    from app.memory.db import get_mysql_uri
    _mysql_saver = AIOMySQLSaver.from_conn_string(get_mysql_uri())
    logger.info("MySQL checkpointer (AIOMySQLSaver) created")
    return _mysql_saver


async def setup_checkpointer() -> None:
    """应用启动时调用, 自动建表。"""
    s = get_settings()
    if s.use_stub_stores:
        return
    saver = _get_mysql_checkpointer()
    await saver.setup()
    logger.info("AIOMySQLSaver.setup() done — checkpoint tables ready")


async def close_checkpointer() -> None:
    global _mysql_saver
    if _mysql_saver is not None:
        # AIOMySQLSaver 实现了 async context manager
        try:
            await _mysql_saver.__aexit__(None, None, None)
        except Exception:
            pass
        _mysql_saver = None
