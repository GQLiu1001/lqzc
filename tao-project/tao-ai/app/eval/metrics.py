from __future__ import annotations

from app.schemas.eval import EvalCaseResult


def _safe_rate(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 1.0
    return float(numerator) / float(denominator)


def compute_metrics(results: list[EvalCaseResult]) -> dict[str, float]:
    total_cases = len(results)
    passed_cases = sum(1 for item in results if item.passed)

    route_scored = [
        item
        for item in results
        if item.expected_agent is not None or item.expected_skill is not None
    ]
    route_accuracy = _safe_rate(
        sum(1 for item in route_scored if item.passed_route),
        len(route_scored),
    )

    tool_calls_total = sum(item.tool_calls_total for item in results)
    tool_calls_success = sum(item.tool_calls_success for item in results)
    tool_success_rate = _safe_rate(tool_calls_success, tool_calls_total)

    retrieval_hit_rate = _safe_rate(sum(1 for item in results if item.retrieval_hits > 0), total_cases)

    predicted_approval = [item for item in results if item.actual_requires_approval]
    true_approval = [
        item
        for item in predicted_approval
        if item.expected_requires_approval is True
    ]
    approval_trigger_precision = _safe_rate(len(true_approval), len(predicted_approval))

    avg_latency_ms = _safe_rate(sum(item.latency_ms for item in results), total_cases)
    pass_rate = _safe_rate(passed_cases, total_cases)

    return {
        "route_accuracy": route_accuracy,
        "tool_success_rate": tool_success_rate,
        "retrieval_hit_rate": retrieval_hit_rate,
        "approval_trigger_precision": approval_trigger_precision,
        "pass_rate": pass_rate,
        "avg_latency_ms": avg_latency_ms,
    }
