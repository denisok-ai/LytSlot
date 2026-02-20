"""
@file: admin.py
@description: Admin - list channels, revenue. Доступ только для ADMIN_TELEGRAM_IDS.
@dependencies: fastapi, db.models
@created: 2025-02-19
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import Channel
from services.api.auth import get_current_admin_user_id
from services.api.deps import get_db_admin

router = APIRouter(prefix="/admin", tags=["admin"])


class ChannelAdminResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    username: str
    slot_duration: int
    price_per_slot: float
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/channels", response_model=list[ChannelAdminResponse], summary="Все каналы (админ)")
def admin_list_channels(
    db: Session = Depends(get_db_admin),
    _admin_id: int = Depends(get_current_admin_user_id),
):
    return [ChannelAdminResponse.model_validate(c) for c in db.query(Channel).all()]


@router.get("/revenue", summary="Выручка (админ)")
def admin_revenue(
    db: Session = Depends(get_db_admin),
    _admin_id: int = Depends(get_current_admin_user_id),
):
    # Placeholder: sum payments or order amounts grouped by tenant
    return {"total_revenue": 0, "by_tenant": []}
