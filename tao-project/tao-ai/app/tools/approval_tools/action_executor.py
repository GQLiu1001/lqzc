from __future__ import annotations

import ast
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from app.memory.mysql_store import MySQLStore
from app.tools.mcp_tools.lqzc_tools import LQZCBusinessTools


logger = logging.getLogger(__name__)

_APPROVAL_ACTION_TOOLS = {
    "submit_refund_for_approval",
    "submit_inventory_adjustment_for_approval",
}


@dataclass(slots=True)
class PlannedAction:
    source_tool: str
    planned_action: dict[str, Any]
    trace_id: int | None = None


class ActionExecutor:
    def __init__(self, *, mysql_store: MySQLStore, business_tools: LQZCBusinessTools) -> None:
        self.mysql_store = mysql_store
        self.business_tools = business_tools

    def execute_task_actions(
        self,
        *,
        task_id: str,
        approval_action: str,
        approver_id: str,
        comment: str | None,
    ) -> dict[str, Any]:
        traces = self.mysql_store.list_tool_traces(task_id=task_id, limit=200)
        planned_actions = self._extract_planned_actions(traces)
        if not planned_actions:
            return {
                "status": "NO_ACTION",
                "message": "no planned action found in tool traces",
                "executions": [],
            }

        executions: list[dict[str, Any]] = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for item in planned_actions:
            canonical_action = self._normalize_action_payload(item.planned_action)
            idempotency_key = self._build_idempotency_key(
                task_id=task_id,
                source_tool=item.source_tool,
                planned_action=canonical_action,
            )

            action_row = self.mysql_store.create_or_get_action_execution(
                task_id=task_id,
                idempotency_key=idempotency_key,
                action_name=item.source_tool,
                action_payload=canonical_action,
                approval_action=approval_action,
                approver_id=approver_id,
                comment=comment,
            )
            execution_id = int(action_row["id"])
            existing_status = str(action_row.get("status") or "").upper()

            if existing_status == "SUCCESS":
                skipped_count += 1
                duplicate_result = {
                    "code": 200,
                    "message": "action already executed, skipped by idempotency",
                    "data": {
                        "idempotency_key": idempotency_key,
                        "execution_id": execution_id,
                    },
                }
                executions.append(
                    {
                        "source_tool": item.source_tool,
                        "status": "SKIPPED_DUPLICATE",
                        "idempotency_key": idempotency_key,
                        "result": duplicate_result,
                    }
                )
                self.mysql_store.insert_tool_trace(
                    task_id=task_id,
                    tool_name=f"execute_{item.source_tool}",
                    arguments={
                        "source_tool": item.source_tool,
                        "idempotency_key": idempotency_key,
                        "mode": "duplicate_skip",
                    },
                    result_preview=json.dumps(duplicate_result, ensure_ascii=False),
                    result=duplicate_result,
                    status="SUCCESS",
                )
                continue

            self.mysql_store.update_action_execution(
                execution_id=execution_id,
                status="RUNNING",
                response=None,
                error_message=None,
            )
            result = self.business_tools.execute_planned_action_sync(
                source_tool=item.source_tool,
                planned_action=canonical_action,
                idempotency_key=idempotency_key,
            )
            result_code = self._safe_int(result.get("code"), default=500)
            status = "SUCCESS" if 200 <= result_code < 400 else "FAILED"

            if status == "SUCCESS":
                success_count += 1
                self.mysql_store.update_action_execution(
                    execution_id=execution_id,
                    status="SUCCESS",
                    response=result,
                    error_message=None,
                )
            else:
                failed_count += 1
                self.mysql_store.update_action_execution(
                    execution_id=execution_id,
                    status="FAILED",
                    response=result,
                    error_message=str(result.get("message") or "unknown execution error"),
                )

            executions.append(
                {
                    "source_tool": item.source_tool,
                    "status": status,
                    "idempotency_key": idempotency_key,
                    "result": result,
                }
            )
            self.mysql_store.insert_tool_trace(
                task_id=task_id,
                tool_name=f"execute_{item.source_tool}",
                arguments={
                    "source_tool": item.source_tool,
                    "idempotency_key": idempotency_key,
                    "planned_action": canonical_action,
                },
                result_preview=json.dumps(result, ensure_ascii=False),
                result=result,
                status=status,
            )

        if failed_count > 0:
            final_status = "FAILED"
        elif success_count > 0:
            final_status = "SUCCESS"
        else:
            final_status = "SKIPPED"

        return {
            "status": final_status,
            "message": (
                f"actions: success={success_count}, failed={failed_count}, skipped={skipped_count}"
            ),
            "executions": executions,
            "summary": {
                "success_count": success_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
                "total_count": len(planned_actions),
            },
        }

    def _extract_planned_actions(self, traces: list[dict[str, Any]]) -> list[PlannedAction]:
        actions: list[PlannedAction] = []
        for row in traces:
            tool_name = str(row.get("tool_name") or "")
            if tool_name not in _APPROVAL_ACTION_TOOLS:
                continue
            payload = self._parse_result_payload(
                raw_result=row.get("result"),
                raw_preview=row.get("result_preview"),
            )
            if not isinstance(payload, dict):
                continue
            data = payload.get("data")
            if not isinstance(data, dict):
                continue
            planned_action = data.get("planned_action")
            if not isinstance(planned_action, dict):
                continue
            actions.append(
                PlannedAction(
                    source_tool=tool_name,
                    planned_action=planned_action,
                    trace_id=int(row["id"]) if row.get("id") is not None else None,
                )
            )
        return actions

    @staticmethod
    def _parse_result_payload(*, raw_result: Any, raw_preview: Any) -> dict[str, Any] | None:
        if isinstance(raw_result, dict):
            return raw_result
        if isinstance(raw_result, str):
            value = raw_result.strip()
            if value:
                try:
                    decoded = json.loads(value)
                    if isinstance(decoded, dict):
                        return decoded
                except Exception:
                    pass

        if not isinstance(raw_preview, str):
            return None
        value = raw_preview.strip()
        if not value:
            return None
        try:
            decoded = json.loads(value)
            if isinstance(decoded, dict):
                return decoded
        except Exception:
            pass
        try:
            decoded = ast.literal_eval(value)
            if isinstance(decoded, dict):
                return decoded
        except Exception:
            pass
        logger.warning("action_executor.parse_preview.failed preview=%s", value[:120])
        return None

    @staticmethod
    def _normalize_action_payload(planned_action: dict[str, Any]) -> dict[str, Any]:
        method = str(planned_action.get("method") or "POST").upper()
        endpoint = str(planned_action.get("endpoint") or "").strip()
        params = planned_action.get("params") if isinstance(planned_action.get("params"), dict) else None
        body = planned_action.get("body") if isinstance(planned_action.get("body"), dict) else None
        normalized: dict[str, Any] = {"method": method, "endpoint": endpoint}
        if params is not None:
            normalized["params"] = params
        if body is not None:
            normalized["body"] = body
        return normalized

    @staticmethod
    def _build_idempotency_key(
        *,
        task_id: str,
        source_tool: str,
        planned_action: dict[str, Any],
    ) -> str:
        payload = json.dumps(planned_action, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        source = f"{task_id}|{source_tool}|{payload}"
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        return f"taoai:{task_id[:12]}:{source_tool}:{digest[:24]}"

    @staticmethod
    def _safe_int(value: Any, *, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default
