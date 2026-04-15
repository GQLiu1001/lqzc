"""提供与过滤相关的实现。"""

from __future__ import annotations


def metadata_filter(*, tenant_id: str | None = None, doc_type: str | None = None) -> str:
    """处理metadata过滤相关逻辑，并返回当前步骤需要的结果。"""
    terms: list[str] = []
    if tenant_id:
        terms.append(f'metadata["tenant_id"] == "{tenant_id}"')
    if doc_type:
        terms.append(f'metadata["doc_type"] == "{doc_type}"')
    return " and ".join(terms)

