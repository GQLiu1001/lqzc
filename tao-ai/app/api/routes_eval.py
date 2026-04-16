"""/eval: 评测接口。

端点:
  POST /eval/run          — 运行评测数据集, 返回 metrics + 明细
  POST /eval/regression   — 运行评测并按阈值做回归 gating
  GET  /eval/datasets     — 列出可用数据集
  POST /eval/index-seed   — 将种子文档写入 Milvus (Milvus 模式下)
  GET  /eval/collections  — 查看 Milvus 各 collection 文档数
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.eval.metrics import compute_all
from app.eval.report import generate_report
from app.eval.runner import DATASET_DIR, load_dataset, run_dataset

router = APIRouter(prefix="/eval", tags=["eval"])
logger = logging.getLogger(__name__)


class EvalRequest(BaseModel):
    dataset: str = "customer_service"
    format: Optional[str] = "json"


class RegressionThresholds(BaseModel):
    skill_accuracy: float = 0.70
    tool_recall: float = 0.60
    tool_precision: float = 0.60
    rag_recall_at_k: float = 0.60
    guardrail_accuracy: float = 1.00
    approval_accuracy: float = 0.80


class RegressionRequest(BaseModel):
    dataset: str = "customer_service"
    thresholds: RegressionThresholds = Field(default_factory=RegressionThresholds)
    format: Optional[str] = "json"


@router.get("/datasets")
async def list_datasets():
    files = sorted(DATASET_DIR.glob("*.jsonl"))
    return {"datasets": [f.stem for f in files]}


@router.post("/run")
async def run_eval(req: EvalRequest):
    try:
        load_dataset(req.dataset)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dataset '{req.dataset}' not found")

    logger.info("eval: starting dataset=%s", req.dataset)
    cases = await run_dataset(req.dataset)
    metrics = compute_all(cases)

    if req.format == "markdown":
        md = generate_report(cases, metrics, req.dataset)
        return {"metrics": metrics, "report_md": md}

    return {
        "metrics": metrics,
        "cases": cases,
    }


@router.post("/regression")
async def run_regression(req: RegressionRequest):
    """线上回归 gating: 跑评测并与阈值比较。"""
    try:
        load_dataset(req.dataset)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dataset '{req.dataset}' not found")

    logger.info("eval: regression starting dataset=%s", req.dataset)
    cases = await run_dataset(req.dataset)
    metrics = compute_all(cases)
    thresholds = req.thresholds.model_dump()

    checks = []
    failed_checks = []
    for metric_name, threshold in thresholds.items():
        actual = float(metrics.get(metric_name, 0.0))
        passed = actual >= float(threshold)
        row = {
            "metric": metric_name,
            "actual": round(actual, 4),
            "threshold": float(threshold),
            "passed": passed,
        }
        checks.append(row)
        if not passed:
            failed_checks.append(row)

    passed = len(failed_checks) == 0
    payload = {
        "dataset": req.dataset,
        "passed": passed,
        "metrics": metrics,
        "thresholds": thresholds,
        "checks": checks,
        "failed_checks": failed_checks,
    }

    if req.format == "markdown":
        report_md = generate_report(cases, metrics, req.dataset)
        gate_md = [
            "## Regression Gate",
            "",
            f"- Passed: {'YES' if passed else 'NO'}",
            f"- Failed checks: {len(failed_checks)}",
        ]
        for row in failed_checks:
            gate_md.append(
                f"- {row['metric']}: actual={row['actual']} < threshold={row['threshold']}"
            )
        payload["report_md"] = report_md
        payload["gate_md"] = "\n".join(gate_md)

    return payload


@router.post("/index-seed")
async def index_seed():
    s = get_settings()
    if not s.milvus_active():
        return {"message": "milvus disabled, seed docs are loaded in-memory automatically", "count": 0}

    from app.retrieval.collections import ensure_collections
    from app.retrieval.indexing import seed_index

    ensure_collections()
    count = seed_index()
    return {"message": f"indexed {count} seed docs into Milvus", "count": count}


@router.get("/collections")
async def collection_stats_endpoint():
    s = get_settings()
    if not s.milvus_active():
        from app.retrieval.indexing import SEED_DOCS
        return {"mode": "stub", "seed_doc_count": len(SEED_DOCS)}

    from app.retrieval.indexing import collection_stats
    return {"mode": "milvus", "stats": collection_stats()}
