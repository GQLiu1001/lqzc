from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.interrupt import router as interrupt_router
from app.core.checkpoint import create_checkpointer
from app.repositories.redis_repo import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield
    await close_redis()


app = FastAPI(title="TAO AI v3 Agent Runtime", lifespan=lifespan)

app.include_router(chat_router)
app.include_router(interrupt_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
