from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings


@asynccontextmanager
async def create_checkpointer():
    async with AsyncPostgresSaver.from_conn_string(settings.postgres_dsn) as checkpointer:
        # For first deployment, this initializes required checkpoint tables.
        await checkpointer.setup()
        yield checkpointer
