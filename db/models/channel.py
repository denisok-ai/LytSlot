"""
@file: channel.py
@description: Channel model - Telegram channel linked to a tenant.
@dependencies: db.base, db.models.tenant
@created: 2025-02-19
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.order import Order
    from db.models.slot import Slot
    from db.models.tenant import Tenant


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slot_duration: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    price_per_slot: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("1000"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="channels")
    slots: Mapped[list[Slot]] = relationship("Slot", back_populates="channel", lazy="selectin")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="channel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Channel id={self.id} username={self.username!r} tenant_id={self.tenant_id}>"
