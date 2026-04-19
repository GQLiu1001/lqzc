"""FastAPI route package for TAO AI v3 chat, interrupt, eval, and rag endpoints."""

from .chat import chat, router as chat_router
from .interrupt import router as interrupt_router, submit_decision
from .rag import rag_reindex, rag_summary, router as rag_router

__all__ = [
    "chat",
    "chat_router",
    "interrupt_router",
    "rag_reindex",
    "rag_router",
    "rag_summary",
    "submit_decision",
]
