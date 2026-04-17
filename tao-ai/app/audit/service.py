import logging

from app.audit.schemas import AuditEvent

logger = logging.getLogger(__name__)


async def record_audit_event(event: AuditEvent) -> None:
    """Persist an audit event to PostgreSQL.

    Currently logs to stdout; will be wired to the audit_log table once
    the repository layer is fully connected.
    """
    logger.info(
        "audit | session=%s user=%s route=%s tool=%s status=%s latency=%sms",
        event.session_id,
        event.user_id,
        event.route,
        event.tool_name,
        event.status,
        event.latency_ms,
    )
