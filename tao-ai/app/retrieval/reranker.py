"""LLM-based Reranker。

初筛 top_k * expand_factor 条 → LLM 打分 → 精排取 top_k。

用 Ollama chat model 做 pointwise 打分:
  对每条候选, 问 LLM "该文档与查询的相关度 0-10 分"。
  解析分数后降序排列, 取 top_k。

Config:
  enable_rerank: bool      是否启用 rerank (默认 True)
  rerank_expand_factor: int 初筛扩展倍数 (默认 3)
"""
from __future__ import annotations

import logging
import re

from langchain_core.messages import SystemMessage

from app.config import get_settings
from app.models.factory import make_chat
from app.schemas.tool import RetrievalHit

logger = logging.getLogger(__name__)

_RERANK_PROMPT = """你是一个相关性打分器。给定用户查询和一段候选文档,请输出一个 0-10 的整数分数表示相关度。
只输出一个数字,不要输出其他内容。

用户查询: {query}
候选文档: {text}

相关度分数 (0-10):"""

_SCORE_RE = re.compile(r"\b(\d{1,2})\b")


async def rerank(
    query: str,
    hits: list[RetrievalHit],
    top_k: int,
) -> list[RetrievalHit]:
    """对候选 hits 做 LLM rerank, 返回精排后的 top_k 条。"""
    s = get_settings()
    if not s.enable_rerank or len(hits) <= top_k:
        return hits[:top_k]

    chat = make_chat(temperature=0.0)
    scored: list[tuple[RetrievalHit, float]] = []

    for hit in hits:
        prompt = _RERANK_PROMPT.format(query=query, text=hit.text[:500])
        try:
            resp = await chat.ainvoke([SystemMessage(content=prompt)])
            content = (resp.content or "").strip() if hasattr(resp, "content") else str(resp)
            m = _SCORE_RE.search(content)
            score = float(m.group(1)) if m else 0.0
            score = min(score, 10.0)
        except Exception as exc:
            logger.warning("rerank: scoring failed for doc=%s: %s", hit.doc_id, exc)
            score = hit.score * 10

        scored.append((hit, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    result = []
    for hit, llm_score in scored[:top_k]:
        result.append(hit.model_copy(update={"score": llm_score / 10.0}))

    logger.info(
        "rerank: %d candidates → top_%d, scores=[%s]",
        len(hits), top_k,
        ", ".join(f"{s:.1f}" for _, s in scored[:top_k]),
    )
    return result
