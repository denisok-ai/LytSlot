"""
@file: deps.py
@description: FastAPI dependencies: DB session with tenant context.
@dependencies: db.database, services.api.auth
@created: 2025-02-19
"""

from uuid import UUID

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import SessionLocal
from services.api.auth import get_current_tenant_id, get_current_user_id, get_optional_tenant_id
from services.api.logging_config import set_tenant_id


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_admin():
    """Сессия БД с отключённым RLS — только для админ-эндпоинтов. Не устанавливает app.tenant_id."""
    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL row_level_security = off"))
        yield db
    finally:
        db.close()


def get_db_with_tenant(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    tenant_id: UUID | None = Depends(get_optional_tenant_id),
):
    """Сессия с установленным app.tenant_id для RLS (если tenant есть в JWT)."""
    from sqlalchemy import text

    set_tenant_id(str(tenant_id) if tenant_id else None)
    if tenant_id is not None:
        db.execute(
            text("SELECT set_config(:key, :val, true)"),
            {"key": "app.tenant_id", "val": str(tenant_id)},
        )
    return db


def get_db_with_required_tenant(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Сессия с обязательным tenant (для маршрутов, где RLS обязателен)."""
    from sqlalchemy import text

    set_tenant_id(str(tenant_id))
    db.execute(
        text("SELECT set_config(:key, :val, true)"), {"key": "app.tenant_id", "val": str(tenant_id)}
    )
    return db
