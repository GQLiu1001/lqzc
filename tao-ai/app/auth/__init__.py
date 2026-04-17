"""Authentication package for resolving Bearer tokens into ``UserContext``."""

from .auth import get_current_user

__all__ = ["get_current_user"]
