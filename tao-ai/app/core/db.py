"""Shared async PostgreSQL pool for audit / eval persistence.

The LangGraph checkpointer owns its own connection via AsyncPostgresSaver.
This pool is for business-side writes (audit_log, eval_run, eval_sample,
online_eval_sample) that should not contend with checkpoint traffic.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None


async def open_db_pool() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = AsyncConnectionPool(
        conninfo=settings.postgres_dsn,
        min_size=1,
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    await _pool.open()
    logger.info("db pool opened: min=1 max=10")


async def close_db_pool() -> None:
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None
    logger.info("db pool closed")


@asynccontextmanager
async def acquire_conn() -> AsyncIterator[psycopg.AsyncConnection]:
    if _pool is None:
        await open_db_pool()
    assert _pool is not None
    async with _pool.connection() as conn:
        yield conn
