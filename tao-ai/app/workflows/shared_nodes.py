"""跨子图复用的通用节点。"""
from __future__ import annotations

import re
from typing import Any

_BLOCK_PATTERNS = [
    re.compile(r"(?i)(ignore\s+previous|系统提示|越狱)"),
]


def guardrail_check(text: str) -> tuple[bool, str]:
    """极简 guardrail: 匹配到禁用模式则返回 (False, reason)。"""
    for pat in _BLOCK_PATTERNS:
        if pat.search(text or ""):
            return False, f"命中 guardrail 规则: {pat.pattern}"
    return True, ""


def truncate(text: str, limit: int = 4000) -> str:
    if text and len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def safe_dump(obj: Any, limit: int = 800) -> str:
    import json

    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    return truncate(s, limit)
