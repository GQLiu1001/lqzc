from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.redis_repo import get_redis
from app.schemas.user import UserContext

_bearer = HTTPBearer()

# Redis key prefixes — mirrors Java backend constants
_STAFF_TOKEN_PREFIX = "login:user:"
_CUSTOMER_TOKEN_PREFIX = "customer:token:"

# Role ID constants from Java ConsulInterceptor (roleId 1 and 2 are staff roles)
_STAFF_ROLE_IDS = {1, 2}

_ROLE_NAMES = {
    1: "staff",
    2: "admin",
}


async def _try_staff_auth(token: str) -> UserContext | None:
    r = await get_redis()
    user_id_str = await r.get(f"{_STAFF_TOKEN_PREFIX}{token}")
    if user_id_str is None:
        return None

    user_id = int(user_id_str)

    # Fetch role info — Java stores user_role in MySQL via MyBatis-Plus.
    # Here we query a lightweight Redis cache that the Java backend maintains,
    # or fall back to a default staff role.
    # For production parity, the Java side should also cache role info in Redis.
    role_key = f"user:role:{user_id}"
    role_id_str = await r.get(role_key)
    role_id = int(role_id_str) if role_id_str else None

    if role_id is not None and role_id not in _STAFF_ROLE_IDS:
        return None

    return UserContext(
        user_type="staff",
        user_id=user_id,
        role=_ROLE_NAMES.get(role_id, "staff") if role_id else "staff",
        role_ids=[role_id] if role_id else [],
    )


async def _try_customer_auth(token: str) -> UserContext | None:
    r = await get_redis()
    customer_id_str = await r.get(f"{_CUSTOMER_TOKEN_PREFIX}{token}")
    if customer_id_str is None:
        return None

    return UserContext(
        user_type="customer",
        user_id=int(customer_id_str),
        role="customer",
    )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UserContext:
    """FastAPI dependency that resolves a Bearer token to a UserContext.

    Tries staff auth first, then customer auth — unified under one Authorization header.
    """
    token = credentials.credentials

    user_ctx = await _try_staff_auth(token)
    if user_ctx is None:
        user_ctx = await _try_customer_auth(token)

    if user_ctx is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    return user_ctx
