"""
@file: main.py
@description: FastAPI app - auth, middleware, routers, WebSocket dashboard.
@dependencies: fastapi, services.api.*
@created: 2025-02-19
"""

import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import Tenant
from services.api.auth import create_access_token, verify_telegram_login_init_data
from services.api.config import settings
from services.api.deps import get_db
from services.api.logging_config import configure_json_logging, get_logger
from services.api.routers import admin, analytics, api_keys, channels, orders, slots, webhooks

configure_json_logging()
logger = get_logger(__name__)


class AuthCallbackBody(BaseModel):
    init_data: str


class DevLoginBody(BaseModel):
    telegram_id: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # shutdown: close redis etc.


OPENAPI_TAGS = [
    {"name": "channels", "description": "Каналы пользователя (Telegram-каналы для рекламы)."},
    {"name": "slots", "description": "Слоты по каналам: создание, список по датам."},
    {"name": "orders", "description": "Заказы на рекламу: создание, список, смена статуса."},
    {"name": "analytics", "description": "Аналитика: сводка, просмотры по дням."},
    {
        "name": "admin",
        "description": "Админ: список каналов, revenue. Доступ только для ADMIN_TELEGRAM_IDS.",
    },
    {"name": "webhooks", "description": "Вебхуки платёжных систем (Stripe, ЮKassa)."},
    {"name": "api-keys", "description": "API-ключи для программного доступа (создание, отзыв)."},
]

app = FastAPI(
    title="LytSlot Pro API",
    description=(
        "REST API мульти-тенантной платформы продажи рекламы в Telegram-каналах. "
        "Авторизация: JWT (Bearer), получение токена через Telegram Login или dev-login. "
        "Все данные изолированы по tenant (RLS)."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
try:
    from services.api.middleware import RateLimitMiddleware, RequestIdMiddleware

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
except Exception:
    logger.warning("Middleware not added", exc_info=True)

app.include_router(channels.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(slots.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(webhooks.router)
app.include_router(analytics.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")


def _telegram_user_name(payload: dict) -> str:
    """Имя для Tenant из init_data (first_name, username или id)."""
    first = payload.get("first_name") or ""
    last = payload.get("last_name") or ""
    if first or last:
        return f"{first} {last}".strip()
    if payload.get("username"):
        return f"@{payload['username']}"
    return payload.get("id") or "User"


@app.post("/api/auth/callback")
def auth_callback(body: AuthCallbackBody, db: Session = Depends(get_db)):
    """
    Telegram Login: проверка initData, создание/получение Tenant, выдача JWT с tenant_id.
    """
    payload = verify_telegram_login_init_data(body.init_data)
    raw_id = payload.get("id") or payload.get("user_id")
    if not raw_id:
        user_json = payload.get("user")
        if user_json:
            try:
                user = json.loads(user_json) if isinstance(user_json, str) else user_json
                raw_id = user.get("id")
            except (json.JSONDecodeError, TypeError):
                pass
    telegram_id = int(raw_id or 0)
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Missing user id in init_data")

    tenant = db.query(Tenant).filter(Tenant.telegram_id == telegram_id).first()
    if not tenant:
        name = _telegram_user_name(payload)
        tenant = Tenant(telegram_id=telegram_id, name=name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    token = create_access_token(telegram_id, tenant_id=tenant.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": str(tenant.id),
    }


@app.post("/api/auth/dev-login")
def dev_login(body: DevLoginBody, db: Session = Depends(get_db)):
    """
    Только для разработки без домена: выдаёт JWT по telegram_id без проверки Telegram.
    Включить: ENABLE_DEV_LOGIN=true в .env (корень проекта). Не использовать в production.
    """
    if not settings.enable_dev_login:
        raise HTTPException(
            status_code=404, detail="Not available. Set ENABLE_DEV_LOGIN=true in root .env"
        )
    telegram_id = body.telegram_id
    if telegram_id <= 0:
        raise HTTPException(status_code=400, detail="telegram_id must be positive")
    try:
        tenant = db.query(Tenant).filter(Tenant.telegram_id == telegram_id).first()
        if not tenant:
            tenant = Tenant(telegram_id=telegram_id, name=f"Dev User {telegram_id}")
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        token = create_access_token(telegram_id, tenant_id=tenant.id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "tenant_id": str(tenant.id),
        }
    except Exception as e:
        logger.exception("dev_login failed")
        raise HTTPException(status_code=500, detail=f"dev_login error: {e!s}") from e


@app.websocket("/ws/dashboard/{tenant_id}")
async def websocket_dashboard(websocket: WebSocket, tenant_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo:{data}")
    except WebSocketDisconnect:
        pass


@app.get("/health")
def health():
    """Liveness: сервис запущен. Не проверяет зависимости."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """
    Readiness: сервис готов принимать трафик.
    Проверяет БД; если задан CELERY_BROKER_URL — также Redis.
    Возвращает 503 при недоступности зависимостей (для k8s/Docker health check).
    """
    from sqlalchemy import text

    from db.database import SessionLocal
    from services.api.config import settings

    checks: dict[str, str] = {}
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e!s}"
    finally:
        db.close()
    if settings.celery_broker_url:
        try:
            import redis

            r = redis.from_url(settings.redis_url)
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e!s}"
    failed = [k for k, v in checks.items() if v != "ok"]
    if failed:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks},
        )
    return {"status": "ready", "checks": checks}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.api.main:app", host=settings.api_host, port=settings.api_port, reload=True
    )
