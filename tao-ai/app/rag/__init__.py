"""RAG package for ingestion, retrieval, filtering, reranking, and formatting.

Submodules are intentionally not imported eagerly here.
`document_repo` depends on `app.rag.chunker`, and eager imports can trigger a
package-level circular import when callers only need a narrow entrypoint such as
`describe_index()` or `load_indexed_chunks()`.
"""

__all__ = [
    "chunker",
    "constants",
    "filters",
    "formatter",
    "ingest",
    "parser",
    "reranker",
    "retriever",
    "service",
]
