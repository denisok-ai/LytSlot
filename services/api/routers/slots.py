"""
@file: slots.py
@description: Slots - list by channel, create (tenant-scoped via channel).
@dependencies: fastapi, db.models, shared.schemas
@created: 2025-02-20
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.models import Channel, Slot, SlotStatus
from services.api.deps import get_db_with_required_tenant
from shared.schemas.slot import SlotCreate, SlotResponse

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("", response_model=list[SlotResponse], summary="Слоты по каналу")
def list_slots(
    channel_id: UUID = Query(..., description="Filter by channel"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: Session = Depends(get_db_with_required_tenant),
):
    q = db.query(Slot).filter(Slot.channel_id == channel_id)
    if date_from is not None:
        q = q.filter(Slot.datetime >= date_from)
    if date_to is not None:
        q = q.filter(Slot.datetime <= date_to)
    slots = q.order_by(Slot.datetime).all()
    return [SlotResponse.model_validate(s) for s in slots]


@router.get("/{slot_id}", response_model=SlotResponse, summary="Слот по ID")
def get_slot(slot_id: UUID, db: Session = Depends(get_db_with_required_tenant)):
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return SlotResponse.model_validate(slot)


@router.post("", response_model=SlotResponse, status_code=201, summary="Создать слот")
def create_slot(body: SlotCreate, db: Session = Depends(get_db_with_required_tenant)):
    ch = db.query(Channel).filter(Channel.id == body.channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    slot = Slot(
        channel_id=body.channel_id,
        datetime=body.datetime,
        status=SlotStatus.FREE,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return SlotResponse.model_validate(slot)
