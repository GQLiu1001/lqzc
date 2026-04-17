from __future__ import annotations

from datetime import datetime

from app.repositories.document_repo import IndexedChunk
from app.schemas.rag import RAGSearchRequest


def build_used_filters(req: RAGSearchRequest) -> dict:
    user_ctx = req.user_context or {}
    return {
        "domain": req.domain,
        "scene": req.scene,
        "user_type": user_ctx.get("user_type"),
        "role": user_ctx.get("role"),
        "tenant_id": user_ctx.get("tenant_id"),
        "warehouse_scope": user_ctx.get("warehouse_scope", []),
        **(req.extra_filters or {}),
    }


def apply_metadata_filters(chunks: list[IndexedChunk], req: RAGSearchRequest) -> list[IndexedChunk]:
    return [chunk for chunk in chunks if _is_chunk_allowed(chunk, req)]


def _is_chunk_allowed(chunk: IndexedChunk, req: RAGSearchRequest) -> bool:
    user_ctx = req.user_context or {}
    metadata = chunk.metadata or {}
    user_type = user_ctx.get("user_type", "customer")
    role = user_ctx.get("role")
    tenant_id = user_ctx.get("tenant_id")
    warehouse_scope = set(user_ctx.get("warehouse_scope", []))

    if chunk.domain != req.domain:
        return False

    if metadata.get("is_active") is False:
        return False

    effective_at = chunk.effective_at
    if effective_at:
        try:
            if datetime.fromisoformat(effective_at) > datetime.now():
                return False
        except ValueError:
            pass

    access_level = metadata.get("access_level")
    if access_level == "staff" and user_type != "staff":
        return False

    role_allowlist = set(metadata.get("role_allowlist", []))
    if role_allowlist and role not in role_allowlist:
        return False

    chunk_tenant = metadata.get("tenant_id")
    if tenant_id and chunk_tenant and chunk_tenant != tenant_id:
        return False

    chunk_scope = set(metadata.get("warehouse_scope", []))
    if chunk_scope and warehouse_scope and not chunk_scope.intersection(warehouse_scope):
        return False

    if req.scene and req.scene != "general":
        chunk_scene = chunk.scene or "general"
        if chunk_scene not in {req.scene, "general"}:
            extra_scenes = req.extra_filters.get("scene_allowlist", []) if req.extra_filters else []
            if chunk_scene not in extra_scenes:
                return False

    for key, expected in (req.extra_filters or {}).items():
        if key == "scene_allowlist":
            continue
        actual = metadata.get(key)
        if expected is None:
            continue
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False

    return True
