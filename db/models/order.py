"""
@file: order.py
@description: Order model - ad order for a slot (advertiser, content, ERID).
@dependencies: db.base, db.models.channel, db.models.slot
@created: 2025-02-19
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.channel import Channel
    from db.models.payment import Payment
    from db.models.slot import Slot


class OrderStatus(enum.StrEnum):
    DRAFT = "draft"
    PAID = "paid"
    MARKED = "marked"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    erid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.DRAFT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    channel: Mapped[Channel] = relationship("Channel", back_populates="orders")
    slot: Mapped[Slot] = relationship("Slot", back_populates="orders")
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="order", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} channel_id={self.channel_id} status={self.status}>"
