"""文档切分 — M8。

包了一层 langchain-text-splitters 的 RecursiveCharacterTextSplitter,
按"段落 → 句号 → 空格 → 字符"逐级回退切分, 中英文友好。

入参 text + 元数据 (source, doc_id_prefix), 输出可直接喂给 index_documents()
的 [{doc_id, text, source}] 列表。
"""
from __future__ import annotations

from typing import Iterable

from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 400
DEFAULT_CHUNK_OVERLAP = 60

_CN_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "!", "?", "；", ";", " ", ""]


def get_splitter(chunk_size: int = DEFAULT_CHUNK_SIZE,
                 chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=_CN_SEPARATORS,
        keep_separator=True,
    )


def chunk_text(
    text: str,
    source: str,
    doc_id_prefix: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """单段长文本 → chunks。"""
    if not text or not text.strip():
        return []
    splitter = get_splitter(chunk_size, chunk_overlap)
    pieces = splitter.split_text(text)
    return [
        {
            "doc_id": f"{doc_id_prefix}-{i:03d}",
            "text": piece.strip(),
            "source": source,
        }
        for i, piece in enumerate(pieces)
        if piece and piece.strip()
    ]


def chunk_documents(
    docs: Iterable[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """对一批 {doc_id, text, source} 文档逐条切分, 子片段 doc_id = 原 id-NNN。

    若原文 <= chunk_size, 直接保留原文档不切分。
    """
    out: list[dict] = []
    for d in docs:
        text = d.get("text", "")
        source = d.get("source", "customer_faq")
        prefix = d.get("doc_id", "doc")
        if len(text) <= chunk_size:
            out.append({"doc_id": prefix, "text": text, "source": source})
            continue
        out.extend(chunk_text(text, source, prefix, chunk_size, chunk_overlap))
    return out
