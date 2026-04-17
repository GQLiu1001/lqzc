"""Repository package.

Submodules are imported on demand (`from app.repositories.redis_repo import ...`)
rather than eagerly, because `document_repo` depends on `app.rag.*` and eager
loading here triggers a circular import through `rag.filters`.
"""
