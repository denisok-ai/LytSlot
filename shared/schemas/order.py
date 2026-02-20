"""
@file: order.py
@description: Order create/response schemas.
@dependencies: pydantic, shared.schemas.tenant
@created: 2025-02-19
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from shared.schemas.tenant import BaseTenantModel


class OrderCreate(BaseModel):
    """Payload to create an order (content + optional erid)."""

    channel_id: UUID
    slot_id: UUID
    content: dict[str, Any] = Field(..., description="Ad content: text, media URLs, etc.")
    erid: str | None = None


class OrderUpdate(BaseModel):
    """Update order status."""

    status: str


class OrderResponse(BaseTenantModel):
    """Order as returned by API."""

    id: UUID
    advertiser_id: int
    channel_id: UUID
    slot_id: UUID
    content: dict[str, Any]
    erid: str | None
    status: str
    created_at: datetime
    updated_at: datetime
