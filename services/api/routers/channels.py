"""
@file: channels.py
@description: Channels CRUD - tenant's channels.
@dependencies: fastapi, db.models, shared.schemas
@created: 2025-02-19
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import Channel
from services.api.auth import get_current_tenant_id
from services.api.deps import get_db_with_required_tenant
from shared.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelResponse], summary="Список каналов")
def list_channels(db: Session = Depends(get_db_with_required_tenant)):
    """Возвращает все каналы текущего tenant."""
    channels = db.query(Channel).all()
    return [ChannelResponse.model_validate(c) for c in channels]


@router.get("/{channel_id}", response_model=ChannelResponse, summary="Канал по ID")
def get_channel(channel_id: UUID, db: Session = Depends(get_db_with_required_tenant)):
    ch = db.query(Channel).filter(Channel.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelResponse.model_validate(ch)


@router.post("", response_model=ChannelResponse, status_code=201, summary="Добавить канал")
def create_channel(
    body: ChannelCreate,
    db: Session = Depends(get_db_with_required_tenant),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    ch = Channel(
        tenant_id=tenant_id,
        username=body.username,
        slot_duration=body.slot_duration,
        price_per_slot=Decimal(str(body.price_per_slot)),
        is_active=body.is_active,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ChannelResponse.model_validate(ch)


@router.patch("/{channel_id}", response_model=ChannelResponse, summary="Обновить канал")
def update_channel(
    channel_id: UUID, body: ChannelUpdate, db: Session = Depends(get_db_with_required_tenant)
):
    ch = db.query(Channel).filter(Channel.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    if body.username is not None:
        ch.username = body.username
    if body.slot_duration is not None:
        ch.slot_duration = body.slot_duration
    if body.price_per_slot is not None:
        ch.price_per_slot = Decimal(str(body.price_per_slot))
    if body.is_active is not None:
        ch.is_active = body.is_active
    db.commit()
    db.refresh(ch)
    return ChannelResponse.model_validate(ch)
