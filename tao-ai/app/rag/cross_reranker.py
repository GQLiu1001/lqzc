"""Qwen3-Reranker 生成式 cross-encoder 封装。

Ollama 不暴露 token logprobs，所以采用二元策略：模型回答 "yes" 记 1.0，"no" 记
0.0，解析失败或超时记 None（视为未决，调用方用词面分做 fallback）。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_RERANK_PROMPT_TEMPLATE = (
    "<|im_start|>system\n"
    "Judge whether the Document meets the requirements based on the Query. "
    'Note that the answer can only be "yes" or "no".<|im_end|>\n'
    "<|im_start|>user\n"
    "<Query>: {query}\n"
    "<Document>: {document}<|im_end|>\n"
    "<|im_start|>assistant\n"
    "<think>\n\n</think>\n\n"
)

_MAX_DOC_CHARS = 1200


def _truncate(text: str, limit: int = _MAX_DOC_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


async def _score_pair(
    client: httpx.AsyncClient,
    query: str,
    document: str,
) -> float | None:
    prompt = _RERANK_PROMPT_TEMPLATE.format(
        query=_truncate(query, 500),
        document=_truncate(document),
    )
    payload = {
        "model": settings.rag_reranker_model,
        "prompt": prompt,
        "stream": False,
        "raw": True,
        "options": {"num_predict": 1, "temperature": 0.0},
    }
    try:
        resp = await client.post("/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("qwen reranker call failed: %s", exc)
        return None

    token = (data.get("response") or "").strip().lower()
    if token.startswith("yes"):
        return 1.0
    if token.startswith("no"):
        return 0.0
    return None


async def score_pairs(
    query: str,
    documents: Iterable[str],
) -> list[float | None]:
    docs = list(documents)
    if not docs:
        return []

    sem = asyncio.Semaphore(max(1, settings.rag_reranker_concurrency))
    timeout = httpx.Timeout(settings.rag_reranker_timeout_seconds)

    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=timeout) as client:
        async def _one(doc: str) -> float | None:
            async with sem:
                return await _score_pair(client, query, doc)

        return await asyncio.gather(*(_one(doc) for doc in docs))
