"""
@file: auth.py
@description: Telegram Login validation + JWT issue/verify.
@dependencies: python-jose, services.api.config
@created: 2025-02-19
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from services.api.config import settings

_http_bearer = HTTPBearer(auto_error=False)


def verify_telegram_login_init_data(init_data: str) -> dict:
    """
    Проверка initData Telegram Login Widget.
    secret_key = HMAC("WebAppData", bot_token); hash = HMAC(secret_key, data_check_string).
    """
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot token not configured")
    try:
        parsed = dict(p.split("=", 1) for p in init_data.split("&") if "=" in p)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid init_data") from None
    hash_val = parsed.pop("hash", None)
    if not hash_val:
        raise HTTPException(status_code=400, detail="Missing hash")
    data_check_string = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))
    secret_key = hmac.new(
        b"WebAppData",
        (
            settings.telegram_bot_token.encode()
            if isinstance(settings.telegram_bot_token, str)
            else settings.telegram_bot_token
        ),
        hashlib.sha256,
    ).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if computed != hash_val:
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")
    auth_date = parsed.get("auth_date")
    if auth_date:
        try:
            ts = int(auth_date)
            if time.time() - ts > settings.auth_date_max_age_seconds:
                raise HTTPException(status_code=401, detail="init_data expired")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid auth_date") from None
    return parsed


def create_access_token(telegram_id: int, tenant_id: UUID | None = None) -> str:
    payload = {
        "sub": str(telegram_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None


def get_user_id_from_token_or_none(token: str | None) -> str | None:
    """Декодирует JWT и возвращает sub (user_id) или None. Для rate limit без исключений."""
    if not token or not token.strip():
        return None
    try:
        payload = jwt.decode(
            token.strip(),
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
    except JWTError:
        return None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> int:
    payload = decode_token(credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(sub)


def get_optional_tenant_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> UUID | None:
    payload = decode_token(credentials)
    tid = payload.get("tenant_id")
    return UUID(tid) if tid else None


def get_current_tenant_id(tenant_id: UUID | None = Depends(get_optional_tenant_id)) -> UUID:
    """Требует авторизации и наличия tenant в JWT (для маршрутов, где RLS обязателен)."""
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not set. Re-login to bind to a tenant.",
        )
    return tenant_id


def get_current_admin_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> int:
    """Требует JWT и вхождения telegram_id (sub) в список ADMIN_TELEGRAM_IDS. Иначе 403."""
    user_id = get_current_user_id(credentials)
    admin_ids = settings.get_admin_telegram_ids()
    if not admin_ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin list not configured (ADMIN_TELEGRAM_IDS).",
        )
    if user_id not in admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user_id
