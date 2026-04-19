from contextvars import ContextVar

from app.schemas.user import UserContext

_user_context_var: ContextVar[UserContext | None] = ContextVar("user_context", default=None)
_session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


def set_user_context(ctx: UserContext) -> None:
    _user_context_var.set(ctx)


def get_user_context() -> UserContext | None:
    return _user_context_var.get()


def set_session_id(sid: str) -> None:
    _session_id_var.set(sid)


def get_session_id() -> str | None:
    return _session_id_var.get()
