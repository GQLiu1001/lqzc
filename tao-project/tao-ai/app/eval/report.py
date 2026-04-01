from __future__ import annotations

from app.schemas.eval import EvalCaseResult, EvalRunSummary


def build_report(summary: EvalRunSummary, results: list[EvalCaseResult]) -> dict:
    failed = [item for item in results if not item.passed]
    top_failed = sorted(failed, key=lambda item: item.latency_ms, reverse=True)[:10]
    return {
        "summary": summary.model_dump(),
        "failures": [
            {
                "case_id": item.case_id,
                "status": item.status,
                "reason": item.error
                or (
                    f"route={item.passed_route}, retrieval={item.passed_retrieval}, "
                    f"approval={item.passed_approval}, keywords={item.passed_keywords}"
                ),
                "latency_ms": item.latency_ms,
            }
            for item in top_failed
        ],
    }
