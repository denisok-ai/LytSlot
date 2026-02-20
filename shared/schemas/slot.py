"""
@file: slot.py
@description: Slot filter, create and response schemas.
@dependencies: pydantic, shared.schemas.tenant
@created: 2025-02-19
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from shared.schemas.tenant import BaseTenantModel


class SlotCreate(BaseModel):
    channel_id: UUID
    datetime: datetime


class SlotFilter(BaseModel):
    """Filter slots by date range and optional channel."""

    date_from: datetime
    date_to: datetime
    channel_id: UUID | None = None


class SlotResponse(BaseTenantModel):
    """Slot as returned by API."""

    id: UUID
    channel_id: UUID
    datetime: datetime
    status: str
    created_at: datetime
