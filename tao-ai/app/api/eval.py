"""Eval REST API — offline run trigger + run/sample查询.

Online eval exposure is deliberately omitted: it is triggered from the live
request path or a scheduled job, not from the external API surface.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import acquire_conn
from app.eval.offline_runner import run_offline_eval

router = APIRouter(prefix="/eval")


class OfflineRunRequest(BaseModel):
    dataset_path: str
    dataset_name: str | None = None


@router.post("/offline/run")
async def offline_run(req: OfflineRunRequest) -> dict:
    try:
        result = await run_offline_eval(req.dataset_path, req.dataset_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result.model_dump(mode="json")


@router.get("/run/{run_id}")
async def get_run(run_id: str) -> dict:
    async with acquire_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM eval_run WHERE run_id=%s", (run_id,))
            run_row = await cur.fetchone()
            if not run_row:
                raise HTTPException(status_code=404, detail=f"eval run {run_id} not found")
            await cur.execute(
                "SELECT sample_id, domain, scene, hit, groundedness, correctness, "
                "permission_safe, passed, failure_reason, latency_ms "
                "FROM eval_sample WHERE run_id=%s ORDER BY sample_id",
                (run_id,),
            )
            sample_rows = await cur.fetchall()
    return {"run": dict(run_row), "samples": [dict(r) for r in sample_rows]}


@router.get("/runs")
async def list_runs(limit: int = 20) -> dict:
    async with acquire_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT run_id, dataset_name, total_samples, hit_at_5, correctness, "
                "groundedness, no_hit_rate, created_at "
                "FROM eval_run ORDER BY created_at DESC LIMIT %s",
                (min(max(limit, 1), 100),),
            )
            rows = await cur.fetchall()
    return {"runs": [dict(r) for r in rows]}
