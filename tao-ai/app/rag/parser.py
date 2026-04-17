from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import re

from app.rag.constants import KnowledgeSource

_MARKDOWN_TITLE_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)


@dataclass(slots=True)
class ParsedDocument:
    doc_id: str
    title: str
    text: str
    path: Path
    domain: str
    scene: str
    source_type: str
    access_level: str
    role_allowlist: tuple[str, ...]
    warehouse_scope: tuple[str, ...]
    version: str
    effective_at: datetime
    metadata: dict[str, object] = field(default_factory=dict)


def parse_document(path: Path, source: KnowledgeSource) -> ParsedDocument | None:
    if not path.exists() or not path.is_file():
        return None

    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = path.read_text(encoding="utf-8", errors="ignore")

    content = normalize_text(raw_text)
    if not content:
        return None

    stat = path.stat()
    updated_at = datetime.fromtimestamp(stat.st_mtime)
    relative_part = path.relative_to(source.root).as_posix()

    return ParsedDocument(
        doc_id=_build_doc_id(source.domain, relative_part),
        title=_extract_title(path, content),
        text=content,
        path=path,
        domain=source.domain,
        scene=resolve_scene(path, source),
        source_type=source.source_type,
        access_level=source.access_level,
        role_allowlist=source.role_allowlist,
        warehouse_scope=source.warehouse_scope,
        version=updated_at.date().isoformat(),
        effective_at=updated_at,
        metadata={
            "source_name": source.name,
            "source_path": str(path),
            "relative_path": relative_part,
            "is_active": True,
            **source.metadata,
        },
    )


def resolve_scene(path: Path, source: KnowledgeSource) -> str:
    if source.scene:
        if source.root.name == "manuals":
            filename = path.stem
            if "售后" in filename:
                return "aftersale_policy"
            if "保养" in filename or "清洁" in filename:
                return "product_consult"
        return source.scene

    parts = path.relative_to(source.root).parts
    if parts:
        if len(parts) > 1:
            return sanitize_name(parts[0])
        return sanitize_name(Path(parts[0]).stem)
    return "general"


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def sanitize_name(value: str) -> str:
    lowered = value.strip().lower().replace(" ", "_").replace("-", "_")
    lowered = re.sub(r"[^a-z0-9_\u4e00-\u9fff]", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered or "general"


def stable_checksum(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _build_doc_id(domain: str, relative_part: str) -> str:
    base = relative_part.rsplit(".", 1)[0]
    return f"{domain}:{sanitize_name(base.replace('/', '_'))}"


def _extract_title(path: Path, content: str) -> str:
    markdown_match = _MARKDOWN_TITLE_PATTERN.search(content)
    if markdown_match:
        return markdown_match.group(1).strip()

    for line in content.splitlines():
        stripped = line.strip().strip("[]【】")
        if stripped:
            return stripped[:80]
    return path.stem
