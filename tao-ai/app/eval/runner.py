"""评测回放 Runner。

加载 JSONL 数据集 → 逐条过 Supervisor Graph → 收集实际输出 → 对比 expected → 返回 annotated cases。

对于需要审批的 case (risk_level=high), runner 只运行到 interrupt 点,
记录是否触发了审批 (approval_triggered), 不执行实际审批。
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.workflows.supervisor_workflow import build_supervisor_graph

logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent / "datasets"


def load_dataset(name: str = "customer_service") -> list[dict[str, Any]]:
    path = DATASET_DIR / f"{name}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: {path}")
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


async def run_single(graph, case: dict[str, Any]) -> dict[str, Any]:
    """运行单条评测用例, 返回 annotated case。"""
    session_id = f"eval-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    init_state = {"user_message": case["query"], "session_id": session_id}

    result = case.copy()
    result["session_id"] = session_id

    try:
        final_result = await graph.ainvoke(init_state, config=config)

        if hasattr(final_result, "value"):
            state = final_result.value
            interrupts = final_result.interrupts
        elif isinstance(final_result, dict):
            state = final_result
            interrupts = ()
        else:
            state = {}
            interrupts = ()

        router = state.get("router")
        result["actual_skill"] = router.skill if router else "unknown"

        planned = state.get("planned_actions", [])
        result["actual_tools"] = [a.get("tool", "") for a in planned]

        rag_hits = state.get("rag_hits", [])
        result["actual_rag_docs"] = [h.get("doc_id", "") for h in rag_hits]

        result["guardrail_blocked"] = not state.get("guardrail_pass", True)

        approval_result = state.get("approval_result", {})
        result["approval_triggered"] = bool(interrupts) or approval_result.get("method") == "human"

        report = state.get("sub_report")
        result["answer"] = state.get("final", "")
        result["success"] = report.success if report else False

    except Exception as exc:
        from langgraph.errors import GraphInterrupt
        if isinstance(exc, GraphInterrupt):
            result["actual_skill"] = "customer_service"
            result["approval_triggered"] = True
            result["answer"] = ""
            result["success"] = True

            snap = await graph.aget_state(config)
            s = snap.values or {}
            result["actual_tools"] = [a.get("tool", "") for a in s.get("planned_actions", [])]
            result["actual_rag_docs"] = [h.get("doc_id", "") for h in s.get("rag_hits", [])]
            result["guardrail_blocked"] = not s.get("guardrail_pass", True)
        else:
            logger.warning("eval case %s failed: %s", case.get("id"), exc)
            result["actual_skill"] = "error"
            result["actual_tools"] = []
            result["actual_rag_docs"] = []
            result["guardrail_blocked"] = False
            result["approval_triggered"] = False
            result["answer"] = f"ERROR: {exc}"
            result["success"] = False

    return result


async def run_dataset(name: str = "customer_service") -> list[dict[str, Any]]:
    """加载数据集并运行全部用例。"""
    cases = load_dataset(name)
    graph = build_supervisor_graph(use_checkpointer=True)
    results = []
    for i, case in enumerate(cases):
        logger.info("eval: running case %d/%d id=%s", i + 1, len(cases), case.get("id"))
        result = await run_single(graph, case)
        results.append(result)
    return results
