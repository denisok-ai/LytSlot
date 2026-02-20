"""
@file: tenant.py
@description: Tenant model - channel owner (multi-tenant isolation).
@dependencies: db.base
@created: 2025-02-19
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.api_key import ApiKey
    from db.models.channel import Channel


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    revenue_share: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.2"), nullable=False
    )
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    channels: Mapped[list[Channel]] = relationship(
        "Channel", back_populates="tenant", lazy="selectin"
    )
    api_keys: Mapped[list[ApiKey]] = relationship(
        "ApiKey", back_populates="tenant", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} telegram_id={self.telegram_id} name={self.name!r}>"
