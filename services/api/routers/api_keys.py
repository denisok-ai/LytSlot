"""
@file: api_keys.py
@description: API keys - list, create (returns raw key once), revoke (tenant-scoped).
@dependencies: fastapi, db.models
@created: 2025-02-20
"""

import hashlib
import secrets
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.models import ApiKey
from services.api.auth import get_current_tenant_id
from services.api.deps import get_db_with_required_tenant

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

PREFIX = "lytslot_"


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_key() -> str:
    return PREFIX + secrets.token_urlsafe(32)


class ApiKeyCreate(BaseModel):
    name: str | None = Field(None, max_length=255)


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str | None
    created_at: datetime
    key_preview: str = "••••"

    class Config:
        from_attributes = True


class ApiKeyCreated(BaseModel):
    id: UUID
    name: str | None
    created_at: datetime
    key: str  # только при создании, больше не показывается


@router.get("", response_model=list[ApiKeyResponse], summary="Список API-ключей")
def list_api_keys(db: Session = Depends(get_db_with_required_tenant)):
    """Все ключи текущего tenant. Полное значение ключа не возвращается."""
    keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return [
        ApiKeyResponse(id=k.id, name=k.name, created_at=k.created_at, key_preview="••••")
        for k in keys
    ]


@router.post("", response_model=ApiKeyCreated, status_code=201, summary="Создать API-ключ")
def create_api_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db_with_required_tenant),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    """Создаёт ключ и возвращает его один раз. Сохраните ключ — повторно он не показывается."""
    raw_key = _generate_key()
    key_hash = _hash_key(raw_key)
    api_key = ApiKey(tenant_id=tenant_id, key_hash=key_hash, name=body.name or None)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        created_at=api_key.created_at,
        key=raw_key,
    )


@router.delete("/{key_id}", status_code=204, summary="Отозвать API-ключ")
def revoke_api_key(key_id: UUID, db: Session = Depends(get_db_with_required_tenant)):
    """Удаляет ключ. Доступ по этому ключу будет отклонён."""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(api_key)
    db.commit()
    return None
