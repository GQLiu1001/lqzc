from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.checkpoint import create_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield


app = FastAPI(title="TAO AI v3 Agent Runtime", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
