from __future__ import annotations

import json
import uuid
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from app.config import settings
from app.schemas.eval import EvalCaseResult, EvalRunSummary
from app.schemas.task import TaskRecord, TaskStatus


class MySQLStore:
    def __init__(self) -> None:
        self._connection_kwargs = {
            "host": settings.mysql_host,
            "port": settings.mysql_port,
            "user": settings.mysql_user,
            "password": settings.mysql_password,
            "database": settings.mysql_db,
            "charset": settings.mysql_charset,
            "cursorclass": DictCursor,
            "autocommit": True,
        }
        self._has_tool_trace_result_json = False
        self._init_schema()

    def _connect(self):
        return pymysql.connect(**self._connection_kwargs)

    def ping(self) -> tuple[bool, str | None]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 AS ok")
                    _ = cur.fetchone()
            return True, None
        except Exception as exc:
            return False, str(exc)

    def _init_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS ai_sessions (
                session_id VARCHAR(64) PRIMARY KEY,
                tenant_id VARCHAR(64) NULL,
                user_id VARCHAR(64) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_messages (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                role VARCHAR(20) NOT NULL,
                content MEDIUMTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_messages_session_id (session_id),
                CONSTRAINT fk_ai_messages_session FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_tasks (
                task_id VARCHAR(64) PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                tenant_id VARCHAR(64) NULL,
                user_id VARCHAR(64) NULL,
                status VARCHAR(32) NOT NULL,
                current_agent VARCHAR(64) NULL,
                current_skill VARCHAR(128) NULL,
                risk_level VARCHAR(16) NOT NULL DEFAULT 'LOW',
                user_message MEDIUMTEXT NULL,
                final_response MEDIUMTEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ai_tasks_session_id (session_id),
                INDEX idx_ai_tasks_status (status),
                CONSTRAINT fk_ai_tasks_session FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_tool_traces (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL,
                tool_name VARCHAR(128) NOT NULL,
                arguments_json JSON NULL,
                result_preview TEXT NULL,
                result_json JSON NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_tool_traces_task_id (task_id),
                CONSTRAINT fk_ai_tool_traces_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_retrieval_traces (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL,
                query_text TEXT NOT NULL,
                domain VARCHAR(64) NOT NULL,
                collection_name VARCHAR(128) NOT NULL,
                hits INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_retrieval_traces_task_id (task_id),
                CONSTRAINT fk_ai_retrieval_traces_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_approvals (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL,
                approval_action VARCHAR(32) NOT NULL,
                approver_id VARCHAR(64) NULL,
                comment TEXT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_ai_approvals_task (task_id),
                CONSTRAINT fk_ai_approvals_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_action_executions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL,
                idempotency_key VARCHAR(128) NOT NULL,
                action_name VARCHAR(128) NOT NULL,
                action_payload_json JSON NULL,
                approval_action VARCHAR(32) NOT NULL,
                approver_id VARCHAR(64) NULL,
                comment TEXT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                response_json JSON NULL,
                error_message TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_ai_action_executions_idem (idempotency_key),
                INDEX idx_ai_action_executions_task_id (task_id),
                CONSTRAINT fk_ai_action_executions_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_eval_runs (
                run_id VARCHAR(64) PRIMARY KEY,
                dataset_name VARCHAR(128) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
                total_cases INT NOT NULL DEFAULT 0,
                passed_cases INT NOT NULL DEFAULT 0,
                route_accuracy DOUBLE NOT NULL DEFAULT 0,
                tool_success_rate DOUBLE NOT NULL DEFAULT 0,
                retrieval_hit_rate DOUBLE NOT NULL DEFAULT 0,
                approval_trigger_precision DOUBLE NOT NULL DEFAULT 0,
                pass_rate DOUBLE NOT NULL DEFAULT 0,
                avg_latency_ms DOUBLE NOT NULL DEFAULT 0,
                error_message TEXT NULL,
                started_at VARCHAR(64) NULL,
                finished_at VARCHAR(64) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ai_eval_runs_dataset (dataset_name),
                INDEX idx_ai_eval_runs_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_eval_case_results (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                run_id VARCHAR(64) NOT NULL,
                case_id VARCHAR(128) NOT NULL,
                message TEXT NOT NULL,
                expected_agent VARCHAR(64) NULL,
                expected_skill VARCHAR(128) NULL,
                expected_requires_approval TINYINT(1) NULL,
                actual_agent VARCHAR(64) NULL,
                actual_skill VARCHAR(128) NULL,
                actual_requires_approval TINYINT(1) NOT NULL DEFAULT 0,
                status VARCHAR(32) NOT NULL,
                retrieval_hits INT NOT NULL DEFAULT 0,
                tool_calls_total INT NOT NULL DEFAULT 0,
                tool_calls_success INT NOT NULL DEFAULT 0,
                latency_ms DOUBLE NOT NULL DEFAULT 0,
                passed_route TINYINT(1) NOT NULL DEFAULT 0,
                passed_retrieval TINYINT(1) NOT NULL DEFAULT 0,
                passed_approval TINYINT(1) NOT NULL DEFAULT 0,
                passed_keywords TINYINT(1) NOT NULL DEFAULT 0,
                passed TINYINT(1) NOT NULL DEFAULT 0,
                error_message TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ai_eval_case_run (run_id),
                INDEX idx_ai_eval_case_case_id (case_id),
                CONSTRAINT fk_ai_eval_case_run FOREIGN KEY (run_id) REFERENCES ai_eval_runs(run_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ]
        with self._connect() as conn:
            with conn.cursor() as cur:
                for sql in statements:
                    cur.execute(sql)
                self._ensure_tool_trace_result_json_column(cur)

    def _column_exists(self, cur: DictCursor, *, table_name: str, column_name: str) -> bool:
        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = %s
            """,
            (self._connection_kwargs["database"], table_name, column_name),
        )
        row = cur.fetchone() or {}
        return int(row.get("total") or 0) > 0

    def _ensure_tool_trace_result_json_column(self, cur: DictCursor) -> None:
        has_column = self._column_exists(cur, table_name="ai_tool_traces", column_name="result_json")
        if not has_column:
            cur.execute(
                """
                ALTER TABLE ai_tool_traces
                ADD COLUMN result_json JSON NULL AFTER result_preview
                """
            )
        self._has_tool_trace_result_json = True

    def ensure_session(self, session_id: str | None, *, tenant_id: str | None, user_id: str | None) -> str:
        resolved = (session_id or "").strip() or uuid.uuid4().hex
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_sessions(session_id, tenant_id, user_id)
                    VALUES(%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        tenant_id = VALUES(tenant_id),
                        user_id = VALUES(user_id)
                    """,
                    (resolved, tenant_id, user_id),
                )
        return resolved

    def append_message(self, *, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ai_messages(session_id, role, content) VALUES(%s, %s, %s)",
                    (session_id, role, content),
                )

    def list_messages(self, *, session_id: str, limit: int = 40) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content, created_at
                    FROM ai_messages
                    WHERE session_id = %s
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (session_id, limit),
                )
                rows = cur.fetchall()
        rows.reverse()
        return rows

    def create_task(
        self,
        *,
        session_id: str,
        tenant_id: str | None,
        user_id: str | None,
        user_message: str,
    ) -> str:
        task_id = uuid.uuid4().hex
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_tasks(task_id, session_id, tenant_id, user_id, status, user_message)
                    VALUES(%s, %s, %s, %s, %s, %s)
                    """,
                    (task_id, session_id, tenant_id, user_id, TaskStatus.NEW.value, user_message),
                )
        return task_id

    def update_task(
        self,
        *,
        task_id: str,
        status: TaskStatus | None = None,
        current_agent: str | None = None,
        current_skill: str | None = None,
        risk_level: str | None = None,
        final_response: str | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status=%s")
            params.append(status.value)
        if current_agent is not None:
            updates.append("current_agent=%s")
            params.append(current_agent)
        if current_skill is not None:
            updates.append("current_skill=%s")
            params.append(current_skill)
        if risk_level is not None:
            updates.append("risk_level=%s")
            params.append(risk_level)
        if final_response is not None:
            updates.append("final_response=%s")
            params.append(final_response)

        if not updates:
            return

        params.append(task_id)
        sql = f"UPDATE ai_tasks SET {', '.join(updates)} WHERE task_id=%s"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))

    def get_task(self, *, task_id: str) -> TaskRecord | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT task_id, session_id, tenant_id, user_id, status,
                           current_agent, current_skill, risk_level,
                           final_response, created_at, updated_at
                    FROM ai_tasks
                    WHERE task_id = %s
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return TaskRecord(
            task_id=row["task_id"],
            session_id=row["session_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            status=TaskStatus(row["status"]),
            current_agent=row["current_agent"],
            current_skill=row["current_skill"],
            risk_level=row["risk_level"] or "LOW",
            final_response=row["final_response"],
            created_at=str(row["created_at"]) if row.get("created_at") else None,
            updated_at=str(row["updated_at"]) if row.get("updated_at") else None,
        )

    def list_tool_traces(self, *, task_id: str, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                if self._has_tool_trace_result_json:
                    select_sql = """
                    SELECT id, task_id, tool_name, arguments_json, result_preview, result_json, status, created_at
                    FROM ai_tool_traces
                    WHERE task_id=%s
                    ORDER BY id ASC
                    LIMIT %s
                    """
                else:
                    select_sql = """
                    SELECT id, task_id, tool_name, arguments_json, result_preview, NULL AS result_json, status, created_at
                    FROM ai_tool_traces
                    WHERE task_id=%s
                    ORDER BY id ASC
                    LIMIT %s
                    """
                cur.execute(
                    select_sql,
                    (task_id, max(1, min(limit, 1000))),
                )
                rows = cur.fetchall()

        traces: list[dict[str, Any]] = []
        for row in rows:
            arguments: dict[str, Any] = {}
            raw_arguments = row.get("arguments_json")
            if isinstance(raw_arguments, dict):
                arguments = raw_arguments
            elif isinstance(raw_arguments, str):
                try:
                    parsed = json.loads(raw_arguments)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    arguments = parsed
            parsed_result: Any | None = None
            raw_result = row.get("result_json")
            if isinstance(raw_result, (dict, list)):
                parsed_result = raw_result
            elif isinstance(raw_result, str):
                try:
                    parsed_result = json.loads(raw_result)
                except Exception:
                    parsed_result = raw_result
            result_preview = str(row.get("result_preview") or "")
            if parsed_result is None and result_preview:
                try:
                    parsed_from_preview = json.loads(result_preview)
                except Exception:
                    parsed_from_preview = None
                if isinstance(parsed_from_preview, (dict, list)):
                    parsed_result = parsed_from_preview
            traces.append(
                {
                    "id": int(row["id"]),
                    "task_id": row["task_id"],
                    "tool_name": row["tool_name"],
                    "arguments": arguments,
                    "result_preview": result_preview,
                    "result": parsed_result,
                    "status": row.get("status") or "UNKNOWN",
                    "created_at": str(row["created_at"]) if row.get("created_at") else None,
                }
            )
        return traces

    def insert_tool_trace(
        self,
        *,
        task_id: str,
        tool_name: str,
        arguments: dict,
        result_preview: str,
        status: str,
        result: Any | None = None,
    ) -> None:
        result_json: str | None = None
        if result is not None:
            try:
                result_json = json.dumps(result, ensure_ascii=False)
            except Exception:
                result_json = json.dumps({"raw_result": str(result)}, ensure_ascii=False)
        with self._connect() as conn:
            with conn.cursor() as cur:
                if self._has_tool_trace_result_json:
                    cur.execute(
                        """
                        INSERT INTO ai_tool_traces(task_id, tool_name, arguments_json, result_preview, result_json, status)
                        VALUES(%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            task_id,
                            tool_name,
                            json.dumps(arguments, ensure_ascii=False),
                            result_preview[:1000],
                            result_json,
                            status,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO ai_tool_traces(task_id, tool_name, arguments_json, result_preview, status)
                        VALUES(%s, %s, %s, %s, %s)
                        """,
                        (task_id, tool_name, json.dumps(arguments, ensure_ascii=False), result_preview[:1000], status),
                    )

    def insert_retrieval_trace(self, *, task_id: str, query_text: str, domain: str, collection_name: str, hits: int) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_retrieval_traces(task_id, query_text, domain, collection_name, hits)
                    VALUES(%s, %s, %s, %s, %s)
                    """,
                    (task_id, query_text, domain, collection_name, hits),
                )

    def create_or_update_approval(self, *, task_id: str, approval_action: str, status: str, approver_id: str | None, comment: str | None) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_approvals(task_id, approval_action, approver_id, comment, status)
                    VALUES(%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        approval_action=VALUES(approval_action),
                        approver_id=VALUES(approver_id),
                        comment=VALUES(comment),
                        status=VALUES(status)
                    """,
                    (task_id, approval_action, approver_id, comment, status),
                )

    def get_approval(self, *, task_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT task_id, approval_action, approver_id, comment, status FROM ai_approvals WHERE task_id=%s",
                    (task_id,),
                )
                return cur.fetchone()

    def create_or_get_action_execution(
        self,
        *,
        task_id: str,
        idempotency_key: str,
        action_name: str,
        action_payload: dict[str, Any],
        approval_action: str,
        approver_id: str | None,
        comment: str | None,
    ) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_action_executions(
                        task_id, idempotency_key, action_name, action_payload_json,
                        approval_action, approver_id, comment, status
                    )
                    VALUES(%s, %s, %s, %s, %s, %s, %s, 'PENDING')
                    ON DUPLICATE KEY UPDATE
                        id = LAST_INSERT_ID(id)
                    """,
                    (
                        task_id,
                        idempotency_key,
                        action_name,
                        json.dumps(action_payload, ensure_ascii=False),
                        approval_action,
                        approver_id,
                        comment,
                    ),
                )
                execution_id = int(cur.lastrowid)
                cur.execute(
                    """
                    SELECT id, task_id, idempotency_key, action_name, action_payload_json,
                           approval_action, approver_id, comment, status, response_json, error_message,
                           created_at, updated_at
                    FROM ai_action_executions
                    WHERE id=%s
                    """,
                    (execution_id,),
                )
                row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"Failed to load action execution row: {idempotency_key}")
        return self._normalize_action_execution_row(row)

    def update_action_execution(
        self,
        *,
        execution_id: int,
        status: str,
        response: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ai_action_executions
                    SET status=%s, response_json=%s, error_message=%s
                    WHERE id=%s
                    """,
                    (
                        status,
                        json.dumps(response, ensure_ascii=False) if response is not None else None,
                        error_message,
                        execution_id,
                    ),
                )

    @staticmethod
    def _normalize_action_execution_row(row: dict[str, Any]) -> dict[str, Any]:
        def _decode(value: Any) -> Any:
            if isinstance(value, (dict, list)):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return value

        return {
            "id": int(row["id"]),
            "task_id": row["task_id"],
            "idempotency_key": row["idempotency_key"],
            "action_name": row["action_name"],
            "action_payload": _decode(row.get("action_payload_json")) or {},
            "approval_action": row["approval_action"],
            "approver_id": row.get("approver_id"),
            "comment": row.get("comment"),
            "status": row.get("status") or "UNKNOWN",
            "response": _decode(row.get("response_json")),
            "error_message": row.get("error_message"),
            "created_at": str(row["created_at"]) if row.get("created_at") else None,
            "updated_at": str(row["updated_at"]) if row.get("updated_at") else None,
        }

    def create_eval_run(self, *, dataset_name: str, total_cases: int) -> str:
        run_id = uuid.uuid4().hex
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_eval_runs(run_id, dataset_name, status, total_cases)
                    VALUES(%s, %s, 'RUNNING', %s)
                    """,
                    (run_id, dataset_name, total_cases),
                )
        return run_id

    def finish_eval_run(self, *, summary: EvalRunSummary) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ai_eval_runs
                    SET
                        status=%s,
                        total_cases=%s,
                        passed_cases=%s,
                        route_accuracy=%s,
                        tool_success_rate=%s,
                        retrieval_hit_rate=%s,
                        approval_trigger_precision=%s,
                        pass_rate=%s,
                        avg_latency_ms=%s,
                        error_message=%s,
                        started_at=%s,
                        finished_at=%s
                    WHERE run_id=%s
                    """,
                    (
                        summary.status,
                        summary.total_cases,
                        summary.passed_cases,
                        summary.route_accuracy,
                        summary.tool_success_rate,
                        summary.retrieval_hit_rate,
                        summary.approval_trigger_precision,
                        summary.pass_rate,
                        summary.avg_latency_ms,
                        summary.error,
                        summary.started_at,
                        summary.finished_at,
                        summary.run_id,
                    ),
                )

    def insert_eval_case_result(self, *, run_id: str, result: EvalCaseResult) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_eval_case_results(
                        run_id, case_id, message,
                        expected_agent, expected_skill, expected_requires_approval,
                        actual_agent, actual_skill, actual_requires_approval,
                        status, retrieval_hits,
                        tool_calls_total, tool_calls_success, latency_ms,
                        passed_route, passed_retrieval, passed_approval, passed_keywords, passed,
                        error_message
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s
                    )
                    """,
                    (
                        run_id,
                        result.case_id,
                        result.message,
                        result.expected_agent,
                        result.expected_skill,
                        int(result.expected_requires_approval) if result.expected_requires_approval is not None else None,
                        result.actual_agent,
                        result.actual_skill,
                        int(result.actual_requires_approval),
                        result.status,
                        result.retrieval_hits,
                        result.tool_calls_total,
                        result.tool_calls_success,
                        result.latency_ms,
                        int(result.passed_route),
                        int(result.passed_retrieval),
                        int(result.passed_approval),
                        int(result.passed_keywords),
                        int(result.passed),
                        result.error,
                    ),
                )

    def list_eval_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        run_id, dataset_name, status, total_cases, passed_cases,
                        route_accuracy, tool_success_rate, retrieval_hit_rate,
                        approval_trigger_precision, pass_rate, avg_latency_ms,
                        started_at, finished_at, error_message
                    FROM ai_eval_runs
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (max(1, min(limit, 200)),),
                )
                rows = cur.fetchall()
        return [self._normalize_eval_run_row(row) for row in rows]

    def get_eval_run(self, *, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        run_id, dataset_name, status, total_cases, passed_cases,
                        route_accuracy, tool_success_rate, retrieval_hit_rate,
                        approval_trigger_precision, pass_rate, avg_latency_ms,
                        started_at, finished_at, error_message
                    FROM ai_eval_runs
                    WHERE run_id=%s
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return self._normalize_eval_run_row(row)

    def list_eval_case_results(self, *, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        case_id, message,
                        expected_agent, expected_skill, expected_requires_approval,
                        actual_agent, actual_skill, actual_requires_approval,
                        status, retrieval_hits, tool_calls_total, tool_calls_success,
                        latency_ms, passed_route, passed_retrieval, passed_approval,
                        passed_keywords, passed, error_message
                    FROM ai_eval_case_results
                    WHERE run_id=%s
                    ORDER BY id ASC
                    """,
                    (run_id,),
                )
                rows = cur.fetchall()

        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "case_id": row["case_id"],
                    "message": row["message"],
                    "expected_agent": row["expected_agent"],
                    "expected_skill": row["expected_skill"],
                    "expected_requires_approval": (
                        bool(row["expected_requires_approval"])
                        if row["expected_requires_approval"] is not None
                        else None
                    ),
                    "actual_agent": row["actual_agent"],
                    "actual_skill": row["actual_skill"],
                    "actual_requires_approval": bool(row["actual_requires_approval"]),
                    "status": row["status"],
                    "retrieval_hits": int(row["retrieval_hits"] or 0),
                    "tool_calls_total": int(row["tool_calls_total"] or 0),
                    "tool_calls_success": int(row["tool_calls_success"] or 0),
                    "latency_ms": float(row["latency_ms"] or 0.0),
                    "passed_route": bool(row["passed_route"]),
                    "passed_retrieval": bool(row["passed_retrieval"]),
                    "passed_approval": bool(row["passed_approval"]),
                    "passed_keywords": bool(row["passed_keywords"]),
                    "passed": bool(row["passed"]),
                    "error": row["error_message"],
                }
            )
        return result

    @staticmethod
    def _normalize_eval_run_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": row["run_id"],
            "dataset_name": row["dataset_name"],
            "status": row["status"],
            "total_cases": int(row["total_cases"] or 0),
            "passed_cases": int(row["passed_cases"] or 0),
            "route_accuracy": float(row["route_accuracy"] or 0.0),
            "tool_success_rate": float(row["tool_success_rate"] or 0.0),
            "retrieval_hit_rate": float(row["retrieval_hit_rate"] or 0.0),
            "approval_trigger_precision": float(row["approval_trigger_precision"] or 0.0),
            "pass_rate": float(row.get("pass_rate") or 0.0),
            "avg_latency_ms": float(row.get("avg_latency_ms") or 0.0),
            "started_at": row.get("started_at"),
            "finished_at": row.get("finished_at"),
            "error": row.get("error_message"),
        }
