import json
import logging
from time import perf_counter

from app.audit.schemas import AuditEvent
from app.core.db import acquire_conn
from app.core.trace import trace_in, trace_out

logger = logging.getLogger(__name__)

_INSERT_SQL = """
INSERT INTO audit_log (
    session_id, message_id, user_type, user_id,
    route, intent, tool_name, tool_args,
    status, error_code, latency_ms
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
ON CONFLICT ON CONSTRAINT idx_audit_session DO NOTHING
"""


async def record_audit_event(event: AuditEvent) -> None:
    """Persist an audit event to agent_db.audit_log.

    Failures are logged but never raised — audit is fire-and-forget from the
    hot request path.
    """
    started = perf_counter()
    trace_in(
        "audit.record_audit_event",
        session_id=event.session_id,
        message_id=event.message_id,
        user_id=event.user_id,
        route=event.route,
        tool=event.tool_name,
        status=event.status,
    )
    try:
        async with acquire_conn() as conn:
            cursor = await conn.execute(
                _INSERT_SQL,
                (
                    event.session_id,
                    event.message_id,
                    event.user_type,
                    event.user_id,
                    event.route,
                    event.intent,
                    event.tool_name,
                    json.dumps(event.tool_args, ensure_ascii=False) if event.tool_args else None,
                    event.status,
                    event.error_code,
                    event.latency_ms,
                ),
            )
            inserted = max(int(cursor.rowcount or 0), 0)
            trace_out(
                "audit.record_audit_event",
                elapsed_ms=int((perf_counter() - started) * 1000),
                inserted=inserted,
                skipped=inserted == 0,
                tool=event.tool_name,
                status=event.status,
            )
    except Exception as exc:
        logger.warning(
            "audit persist failed (%s) session=%s tool=%s status=%s",
            exc,
            event.session_id,
            event.tool_name,
            event.status,
        )
        trace_out(
            "audit.record_audit_event",
            elapsed_ms=int((perf_counter() - started) * 1000),
            inserted=0,
            skipped=False,
            error=str(exc),
            tool=event.tool_name,
            status=event.status,
        )
