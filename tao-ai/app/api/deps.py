"""FastAPI 依赖注入。"""
from __future__ import annotations

from functools import lru_cache

from app.workflows.supervisor_workflow import build_supervisor_graph


@lru_cache(maxsize=1)
def get_supervisor_graph():
    return build_supervisor_graph(use_checkpointer=True)
