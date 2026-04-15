"""提供与routes管理相关的实现。"""

from __future__ import annotations

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import get_runtime_container
from app.config import settings
from app.retrieval.milvus_client import MilvusClient


router = APIRouter(tags=["admin"])


@router.get("/health")
def health() -> dict[str, str]:
    """返回最基础的健康信息。

    这个接口更偏“活着没”，不会深入检查依赖是否真的可用。
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "ollama_model": settings.ollama_chat_model,
        "milvus": f"{settings.milvus_host}:{settings.milvus_port}",
        "mysql": f"{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}",
    }


@router.get("/ready")
async def ready() -> JSONResponse:
    """检查系统是否具备对外提供服务的条件。

    和 `/health` 不同，这里会进一步检查：
    - MySQL
    - Milvus
    - Ollama
    """
    runtime = get_runtime_container()

    mysql_ok, mysql_error = runtime.workflow.memory.mysql.ping()
    milvus_ok, milvus_error = MilvusClient().ping()

    ollama_ok = True
    ollama_error: str | None = None
    try:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception as exc:
        ollama_ok = False
        ollama_error = str(exc)

    # 只有关键依赖都正常，才认为系统 ready。
    overall = mysql_ok and milvus_ok and ollama_ok
    payload = {
        "status": "ready" if overall else "degraded",
        "dependencies": {
            "mysql": {"ok": mysql_ok, "error": mysql_error},
            "milvus": {"ok": milvus_ok, "error": milvus_error},
            "ollama": {"ok": ollama_ok, "error": ollama_error},
        },
    }
    return JSONResponse(status_code=200 if overall else 503, content=payload)
