"""提供与运行器相关的实现。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.eval.datasets import load_dataset
from app.eval.metrics import compute_metrics
from app.eval.replay import replay_case
from app.schemas.eval import EvalCaseResult, EvalRunDetail, EvalRunSummary


if TYPE_CHECKING:
    from app.memory.mysql_store import MySQLStore
    from app.workflows.supervisor_workflow import SupervisorWorkflow


logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO 字符串。"""
    return datetime.now(tz=timezone.utc).isoformat()


class EvalRunner:
    """评测运行器。

    这套评测不是单元测试，而更像“离线回放一批真实/模拟问题，
    看路由、检索、工具、审批触发是否符合预期”。
    """
    def __init__(self, *, workflow: SupervisorWorkflow, mysql_store: MySQLStore) -> None:
        """注入待评测工作流和用于持久化评测结果的存储层。"""
        self.workflow = workflow
        self.mysql_store = mysql_store

    async def run(
        self,
        dataset_name: str,
        *,
        max_cases: int | None = None,
        stop_on_error: bool = False,
        persist: bool = True,
    ) -> EvalRunDetail:
        """执行一轮完整评测。

        流程可以理解成：
        1. 读数据集
        2. 逐条 case 回放
        3. 汇总指标
        4. 按需落库
        """
        cases = load_dataset(dataset_name, max_cases=max_cases)
        started_at = _utc_now_iso()

        # persist=True 时，会把本次评测写入数据库，方便后续查看历史 run。
        run_id = ""
        if persist:
            run_id = self.mysql_store.create_eval_run(dataset_name=dataset_name, total_cases=len(cases))

        logger.info(
            "eval.run.start dataset=%s total_cases=%s persist=%s run_id=%s",
            dataset_name,
            len(cases),
            persist,
            run_id,
        )

        results: list[EvalCaseResult] = []
        run_status = "SUCCESS"
        run_error: str | None = None

        for case in cases:
            # replay_case 会真的调用工作流跑一遍，只是输入来自评测数据集。
            result = await replay_case(self.workflow, case)
            results.append(result)
            if persist:
                self.mysql_store.insert_eval_case_result(run_id=run_id, result=result)
            if stop_on_error and result.error:
                run_status = "FAILED"
                run_error = result.error
                break
            if result.error and run_status == "SUCCESS":
                run_status = "PARTIAL_FAILED"
                run_error = result.error

        # 所有 case 跑完后，再统一计算整体指标。
        metric_map = compute_metrics(results)
        passed_cases = sum(1 for item in results if item.passed)
        finished_at = _utc_now_iso()
        if run_error and run_status != "FAILED":
            run_status = "FAILED"

        summary = EvalRunSummary(
            run_id=run_id or "in_memory",
            dataset_name=dataset_name,
            status=run_status,
            total_cases=len(results),
            passed_cases=passed_cases,
            route_accuracy=metric_map["route_accuracy"],
            tool_success_rate=metric_map["tool_success_rate"],
            retrieval_hit_rate=metric_map["retrieval_hit_rate"],
            approval_trigger_precision=metric_map["approval_trigger_precision"],
            pass_rate=metric_map["pass_rate"],
            avg_latency_ms=metric_map["avg_latency_ms"],
            started_at=started_at,
            finished_at=finished_at,
            error=run_error,
        )

        if persist:
            self.mysql_store.finish_eval_run(summary=summary)

        logger.info(
            "eval.run.finish dataset=%s run_id=%s status=%s pass_rate=%.4f route_accuracy=%.4f",
            dataset_name,
            summary.run_id,
            summary.status,
            summary.pass_rate,
            summary.route_accuracy,
        )
        return EvalRunDetail(summary=summary, cases=results)

    def list_runs(self, *, limit: int = 20) -> list[EvalRunSummary]:
        """列出历史评测任务摘要。"""
        rows = self.mysql_store.list_eval_runs(limit=limit)
        return [EvalRunSummary.model_validate(row) for row in rows]

    def get_run(self, run_id: str) -> EvalRunDetail | None:
        """读取某次评测的摘要和全部 case 结果。"""
        summary_row = self.mysql_store.get_eval_run(run_id=run_id)
        if summary_row is None:
            return None
        case_rows = self.mysql_store.list_eval_case_results(run_id=run_id)
        return EvalRunDetail(
            summary=EvalRunSummary.model_validate(summary_row),
            cases=[EvalCaseResult.model_validate(row) for row in case_rows],
        )
