"""Online eval worker — samples live traffic for judge scoring.

The audit_log captures the metadata for each /chat request (session, route,
tools, status, latency) but not the full question/answer text. Online eval
therefore needs the caller to supply `question`, `answer`, and `context_text`
when it judges a sample — typically pulled from a live message trace table
or forwarded directly from the /chat hot path.

`sample_recent_audit` returns candidate rows; `judge_and_persist` scores one
sample via the full_judge pipeline and writes the result into
online_eval_sample.
"""

from __future__ import annotations

import json
import logging
import random

from app.core.db import acquire_conn
from app.eval.judges import full_judge
from app.eval.schemas import EvalSample

logger = logging.getLogger(__name__)


async def sample_recent_audit(
    *,
    limit: int = 50,
    sample_rate: float = 1.0,
    route: str | None = None,
    hours: int = 24,
) -> list[dict]:
    """Pick recent audit_log rows as online-eval candidates."""
    params: list = []
    where = ["created_at > NOW() - (%s || ' hours')::interval"]
    params.append(str(hours))
    if route:
        where.append("route = %s")
        params.append(route)
    sql = f"""
        SELECT session_id, message_id, route, intent, tool_name, tool_args,
               status, latency_ms, user_type, user_id, created_at
        FROM audit_log
        WHERE {' AND '.join(where)}
        ORDER BY created_at DESC
        LIMIT %s
    """
    params.append(limit)
    async with acquire_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

    picks: list[dict] = []
    for row in rows:
        if sample_rate < 1.0 and random.random() > sample_rate:
            continue
        picks.append(dict(row))
    return picks


_INSERT_ONLINE = """
INSERT INTO online_eval_sample (
    session_id, message_id, route, intent, question, answer, tool_calls,
    retrieved_docs, no_hit, latency_ms, status, user_context,
    rule_judge_pass, rule_judge_detail, llm_judge_score, llm_judge_detail,
    failed, failure_tags
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb,
          %s, %s::jsonb, %s, %s::jsonb, %s, %s)
"""


async def judge_and_persist(
    *,
    audit_row: dict,
    question: str,
    answer: str,
    context_text: str = "",
    retrieved_doc_ids: list[str] | None = None,
) -> dict:
    """Run full_judge on a live sample and persist to online_eval_sample."""
    sample = EvalSample(
        id=audit_row.get("message_id") or audit_row["session_id"],
        domain=audit_row.get("route") or "shared",
        scene=audit_row.get("intent"),
        question=question,
        user_context={
            "user_type": audit_row.get("user_type"),
            "user_id": audit_row.get("user_id"),
        },
    )
    judge = await full_judge(sample, answer, context_text)

    failure_tags: list[str] = []
    if not judge.rule_pass:
        failure_tags.append("rule")
    if not judge.permission_safe:
        failure_tags.append("permission")
    if judge.correctness < 0.5:
        failure_tags.append("correctness_low")
    if judge.groundedness < 0.5:
        failure_tags.append("groundedness_low")
    failed = bool(failure_tags)
    llm_score = round((judge.correctness + judge.groundedness) / 2, 4)

    tool_calls = (audit_row.get("tool_args") or {}).get("tool_calls") or []
    no_hit = not retrieved_doc_ids

    try:
        async with acquire_conn() as conn:
            await conn.execute(
                _INSERT_ONLINE,
                (
                    audit_row["session_id"],
                    audit_row.get("message_id"),
                    audit_row.get("route"),
                    audit_row.get("intent"),
                    question,
                    answer,
                    tool_calls,
                    json.dumps(
                        {"retrieved_doc_ids": retrieved_doc_ids or []},
                        ensure_ascii=False,
                    ),
                    no_hit,
                    audit_row.get("latency_ms"),
                    audit_row.get("status"),
                    json.dumps(sample.user_context),
                    judge.rule_pass,
                    json.dumps(judge.rule_detail, ensure_ascii=False),
                    llm_score,
                    json.dumps(judge.llm_detail, ensure_ascii=False),
                    failed,
                    failure_tags,
                ),
            )
    except Exception:
        logger.exception("online eval persist failed session=%s", audit_row.get("session_id"))

    return {
        "rule_pass": judge.rule_pass,
        "correctness": judge.correctness,
        "groundedness": judge.groundedness,
        "permission_safe": judge.permission_safe,
        "failed": failed,
        "failure_tags": failure_tags,
    }
