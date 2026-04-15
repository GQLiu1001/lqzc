"""提供与回放相关的实现。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from app.schemas.api import ChatRequest
from app.schemas.eval import EvalCase, EvalCaseResult


if TYPE_CHECKING:
    from app.workflows.supervisor_workflow import SupervisorWorkflow


def _keyword_pass(answer: str, case: EvalCase) -> bool:
    """检查回答内容是否满足关键词预期。"""
    expected = case.expected
    text = answer.lower().strip()
    if not text:
        return False if (expected.must_include_keywords or expected.any_of_keywords) else True

    must_include = expected.must_include_keywords
    if must_include:
        for keyword in must_include:
            if keyword.lower() not in text:
                return False

    any_of = expected.any_of_keywords
    if any_of:
        return any(keyword.lower() in text for keyword in any_of)
    return True


def _route_pass(case: EvalCase, *, actual_agent: str) -> bool:
    """检查路由结果是否符合预期 agent。"""
    expected = case.expected
    if expected.agent and expected.agent != actual_agent:
        return False
    return True


def _approval_pass(case: EvalCase, *, actual_requires_approval: bool) -> bool:
    """检查审批触发结果是否符合预期。"""
    expected_value = case.expected.requires_approval
    if expected_value is None:
        return True
    return expected_value == actual_requires_approval


def _retrieval_pass(case: EvalCase, *, retrieval_hits: int) -> bool:
    """检查检索命中数是否达到最低要求。"""
    threshold = case.expected.min_evidence_hits
    if threshold is None:
        threshold = 1
    return retrieval_hits >= threshold


async def replay_case(workflow: SupervisorWorkflow, case: EvalCase) -> EvalCaseResult:
    """回放单条评测用例。

    它会真的走一遍生产工作流，只是输入来自测试数据集。
    最后再把实际输出和期望结果进行比对，生成 `EvalCaseResult`。
    """
    payload = ChatRequest(
        session_id=case.session_id,
        tenant_id=case.tenant_id,
        user_id=case.user_id,
        message=case.message,
        context=case.context,
    )
    started = time.perf_counter()
    try:
        _, _, output = await workflow.run_chat(payload)
    except Exception as exc:
        # 如果工作流直接抛异常，这条 case 视为失败，并把错误记进结果里。
        return EvalCaseResult(
            case_id=case.case_id,
            message=case.message,
            expected_agent=case.expected.agent,
            expected_requires_approval=case.expected.requires_approval,
            status="FAILED",
            latency_ms=max(0.0, (time.perf_counter() - started) * 1000.0),
            error=str(exc),
        )

    latency_ms = max(0.0, (time.perf_counter() - started) * 1000.0)
    # 下面这些字段就是后面算评测指标时要用到的基础统计量。
    retrieval_hits = len(output.evidence)
    tool_calls_total = len(output.tool_trace)
    tool_calls_success = sum(1 for item in output.tool_trace if item.status.upper().startswith("SUCCESS"))

    passed_route = _route_pass(case, actual_agent=output.agent)
    passed_approval = _approval_pass(case, actual_requires_approval=output.requires_approval)
    passed_retrieval = _retrieval_pass(case, retrieval_hits=retrieval_hits)
    passed_keywords = _keyword_pass(output.answer, case)
    passed = passed_route and passed_approval and passed_retrieval and passed_keywords and output.status != "FAILED"

    return EvalCaseResult(
        case_id=case.case_id,
        message=case.message,
        expected_agent=case.expected.agent,
        expected_requires_approval=case.expected.requires_approval,
        actual_agent=output.agent,
        actual_requires_approval=output.requires_approval,
        status=output.status,
        retrieval_hits=retrieval_hits,
        tool_calls_total=tool_calls_total,
        tool_calls_success=tool_calls_success,
        latency_ms=latency_ms,
        passed_route=passed_route,
        passed_retrieval=passed_retrieval,
        passed_approval=passed_approval,
        passed_keywords=passed_keywords,
        passed=passed,
    )
