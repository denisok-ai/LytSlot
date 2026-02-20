"""
@file: channel.py
@description: Channel create/update/response schemas.
@dependencies: pydantic
@created: 2025-02-20
"""

from uuid import UUID

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    slot_duration: int = Field(
        default=3600, ge=900, le=86400, description="Seconds (15/30/60 min typical)"
    )
    price_per_slot: float = Field(default=1000.0, ge=0)
    is_active: bool = True


class ChannelUpdate(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=255)
    slot_duration: int | None = Field(None, ge=900, le=86400)
    price_per_slot: float | None = Field(None, ge=0)
    is_active: bool | None = None


class ChannelResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    username: str
    slot_duration: int
    price_per_slot: float
    is_active: bool

    model_config = {"from_attributes": True}
