"""Offline eval runner.

Given a JSONL golden dataset:
  1. run RAG retrieval for each sample,
  2. generate a grounded answer via Ollama,
  3. rule-judge + LLM-judge correctness / groundedness / permission,
  4. aggregate Hit@5 / Recall@10 / MRR / NDCG@10 / groundedness / correctness,
  5. persist run + sample rows into agent_db.eval_run / eval_sample.
"""

from __future__ import annotations

import json
import logging
import math
import time
import uuid
from pathlib import Path

from langchain_ollama import ChatOllama

from app.core.config import settings
from app.core.db import acquire_conn
from app.eval.dataset_loader import load_jsonl
from app.eval.judges import full_judge
from app.eval.schemas import (
    EvalRunResult,
    EvalSample,
    EvalSampleResult,
    JudgeScore,
    RetrievalMetrics,
)
from app.rag.service import get_rag_service
from app.schemas.rag import RAGSearchRequest

logger = logging.getLogger(__name__)

_ANSWER_PROMPT = """\
你是领域客服助手。仅基于下面检索到的上下文片段回答用户问题；如果上下文不足以回答，请明确说明"当前知识库未检索到足够依据"，不要编造。

上下文：
{context}

用户问题：{question}

回答："""


async def _generate_grounded_answer(question: str, context_text: str) -> str:
    if not (context_text or "").strip():
        return "当前知识库未检索到足够依据。"
    llm = ChatOllama(
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
    )
    resp = await llm.ainvoke(
        _ANSWER_PROMPT.format(context=context_text[:3000], question=question)
    )
    return resp.content.strip()


def _compute_retrieval_metrics(
    expected: list[str],
    retrieved: list[str],
    k_hit: int = 5,
    k_recall: int = 10,
    k_ndcg: int = 10,
) -> RetrievalMetrics:
    if not expected:
        # No ground truth → we can only report whether retrieval returned anything.
        return RetrievalMetrics(no_hit=not retrieved, retrieved_doc_ids=retrieved)

    expected_set = set(expected)

    hit_at_k: int | None = None
    for idx, doc_id in enumerate(retrieved[:k_hit], start=1):
        if doc_id in expected_set:
            hit_at_k = idx
            break

    mrr = 0.0
    for idx, doc_id in enumerate(retrieved, start=1):
        if doc_id in expected_set:
            mrr = 1.0 / idx
            break

    top_recall = retrieved[:k_recall]
    recall = (
        sum(1 for d in top_recall if d in expected_set) / len(expected_set)
        if expected_set
        else 0.0
    )

    dcg = 0.0
    for idx, doc_id in enumerate(retrieved[:k_ndcg], start=1):
        rel = 1.0 if doc_id in expected_set else 0.0
        dcg += rel / math.log2(idx + 1)
    ideal_len = min(len(expected_set), k_ndcg)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_len + 1))
    ndcg = (dcg / ideal) if ideal else 0.0

    return RetrievalMetrics(
        hit=hit_at_k is not None,
        hit_at_k=hit_at_k,
        recall=round(recall, 4),
        mrr=round(mrr, 4),
        ndcg=round(ndcg, 4),
        no_hit=not retrieved,
        retrieved_doc_ids=retrieved,
    )


async def _evaluate_sample(sample: EvalSample) -> EvalSampleResult:
    started = time.perf_counter()
    search = await get_rag_service().search(
        RAGSearchRequest(
            domain=sample.domain,
            scene=sample.scene or "general",
            query=sample.question,
            user_context=sample.user_context,
        )
    )
    retrieved_doc_ids = [hit.doc_id for hit in search.hits]
    retrieval = _compute_retrieval_metrics(sample.expected_doc_ids, retrieved_doc_ids)

    answer = await _generate_grounded_answer(sample.question, search.context_text)
    judge = await full_judge(sample, answer, search.context_text)

    reasons: list[str] = []
    if sample.expected_doc_ids and not retrieval.hit:
        reasons.append("retrieval_miss")
    if not judge.rule_pass:
        reasons.append("rule_violation")
    if not judge.permission_safe:
        reasons.append("permission_unsafe")
    if judge.correctness < 0.6:
        reasons.append(f"correctness<{judge.correctness:.2f}")
    if judge.groundedness < 0.6:
        reasons.append(f"groundedness<{judge.groundedness:.2f}")

    passed = not reasons

    return EvalSampleResult(
        sample_id=sample.id,
        domain=sample.domain,
        scene=sample.scene,
        question=sample.question,
        user_context=sample.user_context,
        reference_answer=sample.reference_answer,
        actual_answer=answer,
        retrieved=retrieval,
        judge=judge,
        latency_ms=int((time.perf_counter() - started) * 1000),
        passed=passed,
        failure_reason=",".join(reasons) if reasons else None,
    )


def _aggregate(samples: list[EvalSampleResult]) -> dict:
    n = len(samples) or 1
    return {
        "hit_at_5": round(sum(1 for r in samples if r.retrieved.hit) / n, 4),
        "recall_at_10": round(sum(r.retrieved.recall for r in samples) / n, 4),
        "mrr": round(sum(r.retrieved.mrr for r in samples) / n, 4),
        "ndcg_at_10": round(sum(r.retrieved.ndcg for r in samples) / n, 4),
        "groundedness": round(sum(r.judge.groundedness for r in samples) / n, 4),
        "correctness": round(sum(r.judge.correctness for r in samples) / n, 4),
        "permission_safety": round(sum(1 for r in samples if r.judge.permission_safe) / n, 4),
        "no_hit_rate": round(sum(1 for r in samples if r.retrieved.no_hit) / n, 4),
    }


async def run_offline_eval(dataset_path: str, dataset_name: str | None = None) -> EvalRunResult:
    samples = load_jsonl(dataset_path)
    run_id = f"eval-{uuid.uuid4().hex[:12]}"
    dataset_name = dataset_name or Path(dataset_path).stem

    overall_started = time.perf_counter()
    sample_results: list[EvalSampleResult] = []
    for sample in samples:
        try:
            sample_results.append(await _evaluate_sample(sample))
        except Exception:
            logger.exception("offline eval sample failed id=%s", sample.id)
            sample_results.append(
                EvalSampleResult(
                    sample_id=sample.id,
                    domain=sample.domain,
                    scene=sample.scene,
                    question=sample.question,
                    user_context=sample.user_context,
                    reference_answer=sample.reference_answer,
                    actual_answer="",
                    retrieved=RetrievalMetrics(),
                    judge=JudgeScore(rule_pass=False, permission_safe=True),
                    latency_ms=0,
                    passed=False,
                    failure_reason="runner_error",
                )
            )

    metrics = _aggregate(sample_results)
    result = EvalRunResult(
        run_id=run_id,
        dataset_name=dataset_name,
        total_samples=len(sample_results),
        duration_ms=int((time.perf_counter() - overall_started) * 1000),
        samples=sample_results,
        **metrics,
    )
    await _persist_run(result)
    return result


_RUN_INSERT = """
INSERT INTO eval_run (
    run_id, dataset_name, total_samples,
    hit_at_5, recall_at_10, mrr, ndcg_at_10,
    groundedness, correctness, permission_safety, no_hit_rate,
    duration_ms, config_snapshot
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
"""

_SAMPLE_INSERT = """
INSERT INTO eval_sample (
    run_id, sample_id, domain, scene, question, user_context,
    expected_doc_ids, reference_answer, actual_answer,
    retrieved_docs, hit, groundedness, correctness, permission_safe,
    latency_ms, passed, failure_reason
) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
"""


async def _persist_run(result: EvalRunResult) -> None:
    config_snapshot = {
        "chat_model": settings.ollama_chat_model,
        "embed_model": settings.ollama_embed_model,
        "top_k": settings.rag_default_top_k,
        "rag_min_score": settings.rag_min_score,
        "rag_min_rerank_score": settings.rag_min_rerank_score,
    }
    try:
        async with acquire_conn() as conn:
            await conn.execute(
                _RUN_INSERT,
                (
                    result.run_id,
                    result.dataset_name,
                    result.total_samples,
                    result.hit_at_5,
                    result.recall_at_10,
                    result.mrr,
                    result.ndcg_at_10,
                    result.groundedness,
                    result.correctness,
                    result.permission_safety,
                    result.no_hit_rate,
                    result.duration_ms,
                    json.dumps(config_snapshot),
                ),
            )
            for r in result.samples:
                retrieved_payload = {
                    "retrieved_doc_ids": r.retrieved.retrieved_doc_ids,
                    "hit_at_k": r.retrieved.hit_at_k,
                    "recall": r.retrieved.recall,
                    "mrr": r.retrieved.mrr,
                    "ndcg": r.retrieved.ndcg,
                    "rule_detail": r.judge.rule_detail,
                    "llm_detail": r.judge.llm_detail,
                }
                await conn.execute(
                    _SAMPLE_INSERT,
                    (
                        result.run_id,
                        r.sample_id,
                        r.domain,
                        r.scene,
                        r.question,
                        json.dumps(r.user_context, ensure_ascii=False),
                        r.retrieved.retrieved_doc_ids,
                        r.reference_answer,
                        r.actual_answer,
                        json.dumps(retrieved_payload, ensure_ascii=False),
                        r.retrieved.hit,
                        r.judge.groundedness,
                        r.judge.correctness,
                        r.judge.permission_safe,
                        r.latency_ms,
                        r.passed,
                        r.failure_reason,
                    ),
                )
    except Exception:
        logger.exception("eval persist failed run_id=%s", result.run_id)
