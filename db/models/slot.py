"""
@file: slot.py
@description: Slot model - time slot for ad placement in a channel.
@dependencies: db.base, db.models.channel
@created: 2025-02-19
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.channel import Channel
    from db.models.order import Order


class SlotStatus(enum.StrEnum):
    FREE = "free"
    RESERVED = "reserved"
    PAID = "paid"
    BLOCKED = "blocked"


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    datetime: Mapped[dt] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, values_callable=lambda x: [e.value for e in x]),
        default=SlotStatus.FREE,
        nullable=False,
    )
    created_at: Mapped[dt] = mapped_column(DateTime(timezone=True), default=dt.utcnow)

    channel: Mapped[Channel] = relationship("Channel", back_populates="slots")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="slot", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Slot id={self.id} channel_id={self.channel_id} "
            f"datetime={self.datetime} status={self.status}>"
        )
