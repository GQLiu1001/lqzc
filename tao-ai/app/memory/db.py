"""异步 MySQL 连接池管理。

M2: 提供全局连接池, 供 TaskRepo / AIOMySQLSaver 共用。
use_stub_stores=True 时不初始化连接池。
"""
from __future__ import annotations

import logging
from typing import Optional

import aiomysql

from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    global _pool
    if _pool is not None:
        return _pool
    s = get_settings()
    _pool = await aiomysql.create_pool(
        host=s.mysql_host,
        port=s.mysql_port,
        user=s.mysql_user,
        password=s.mysql_password,
        db=s.mysql_db,
        charset=s.mysql_charset,
        autocommit=True,
        minsize=2,
        maxsize=10,
    )
    logger.info("MySQL pool created host=%s db=%s", s.mysql_host, s.mysql_db)
    return _pool


def get_mysql_uri() -> str:
    s = get_settings()
    return (
        f"mysql+aiomysql://{s.mysql_user}:{s.mysql_password}"
        f"@{s.mysql_host}:{s.mysql_port}/{s.mysql_db}"
        f"?charset={s.mysql_charset}"
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("MySQL pool closed")
