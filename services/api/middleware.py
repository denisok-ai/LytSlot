"""
@file: middleware.py
@description: Request ID, tenant context and rate limit middleware.
@dependencies: fastapi, redis, services.api.config, services.api.logging_config
@created: 2025-02-19
"""

import uuid
from uuid import UUID

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from services.api.config import settings
from services.api.logging_config import get_logger, set_request_id

_redis: redis.Redis | None = None
logger = get_logger(__name__)


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url)
    return _redis


REQUEST_ID_HEADER = "X-Request-Id"
RESPONSE_REQUEST_ID_HEADER = "X-Request-Id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Генерирует или прокидывает X-Request-Id, кладёт в request.state и контекст логов."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)
        response = await call_next(request)
        response.headers[RESPONSE_REQUEST_ID_HEADER] = request_id
        return response


class TenantMiddleware(BaseHTTPMiddleware):
    """Set app.tenant_id in DB session from JWT (handled in dependencies, not here)."""

    async def dispatch(self, request: Request, call_next):
        return await call_next(request)


def _rate_limit_key(request: Request) -> str:
    """Ключ для rate limit: по user_id из JWT (Bearer), иначе по IP."""
    from services.api.auth import get_user_id_from_token_or_none

    auth = request.headers.get("Authorization") or ""
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        user_id = get_user_id_from_token_or_none(token)
        if user_id:
            return f"user:{user_id}"
    ip = request.client.host if request.client else "anon"
    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Лимит запросов в минуту по пользователю (JWT sub) или по IP. Redis, окно 60 сек."""

    async def dispatch(self, request: Request, call_next):
        key = _rate_limit_key(request)
        redis_key = f"rate:{key}"
        try:
            r = await get_redis()
            n = await r.incr(redis_key)
            if n == 1:
                await r.expire(redis_key, 60)
            if n > settings.rate_limit_per_minute:
                return Response(
                    status_code=429,
                    content="Too Many Requests",
                    headers={"Retry-After": "60"},
                )
        except Exception:
            pass
        return await call_next(request)


def set_tenant_id_for_session(tenant_id: UUID | None) -> str:
    """Return SQL to set app.tenant_id for current session (call before DB ops)."""
    if tenant_id is None:
        return "SELECT set_config('app.tenant_id', '', true)"
    return f"SELECT set_config('app.tenant_id', '{tenant_id}', true)"
