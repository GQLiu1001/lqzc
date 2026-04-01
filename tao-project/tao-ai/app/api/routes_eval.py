from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.api.deps import get_runtime_container
from app.config import settings
from app.eval.datasets import list_datasets
from app.schemas.api import EvalRunRequest, EvalRunResponse
from app.schemas.eval import EvalRunDetail, EvalRunSummary


router = APIRouter(tags=["eval"])
logger = logging.getLogger(__name__)


def _ensure_eval_enabled() -> None:
    if settings.enable_eval:
        return
    raise HTTPException(status_code=503, detail="Eval is disabled by config")


@router.post("/eval/run", response_model=EvalRunResponse)
async def run_eval(payload: EvalRunRequest) -> EvalRunResponse:
    _ensure_eval_enabled()
    runtime = get_runtime_container()
    try:
        detail = await runtime.eval_runner.run(
            payload.dataset_name,
            max_cases=payload.max_cases,
            stop_on_error=payload.stop_on_error,
            persist=payload.persist,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(
        "eval.api.run dataset=%s run_id=%s status=%s total=%s passed=%s",
        detail.summary.dataset_name,
        detail.summary.run_id,
        detail.summary.status,
        detail.summary.total_cases,
        detail.summary.passed_cases,
    )
    return EvalRunResponse.from_summary(detail.summary, include_cases=True, cases=detail.cases)


@router.get("/eval/datasets", response_model=list[str])
def get_eval_datasets() -> list[str]:
    _ensure_eval_enabled()
    datasets = list_datasets()
    logger.info("eval.api.datasets count=%s", len(datasets))
    return datasets


@router.get("/eval/runs", response_model=list[EvalRunSummary])
def get_eval_runs(limit: int = 20) -> list[EvalRunSummary]:
    _ensure_eval_enabled()
    runtime = get_runtime_container()
    runs = runtime.eval_runner.list_runs(limit=limit)
    logger.info("eval.api.runs count=%s limit=%s", len(runs), limit)
    return runs


@router.get("/eval/runs/{run_id}", response_model=EvalRunDetail)
def get_eval_run(run_id: str) -> EvalRunDetail:
    _ensure_eval_enabled()
    runtime = get_runtime_container()
    detail = runtime.eval_runner.get_run(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Eval run not found")
    logger.info(
        "eval.api.run_detail run_id=%s total=%s passed=%s",
        detail.summary.run_id,
        detail.summary.total_cases,
        detail.summary.passed_cases,
    )
    return detail
