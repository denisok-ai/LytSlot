"""
@file: __init__.py
@description: Export shared Pydantic schemas for API/bot/worker.
@dependencies: shared.schemas.*
@created: 2025-02-19
"""

from shared.schemas.channel import ChannelCreate, ChannelUpdate
from shared.schemas.channel import ChannelResponse as ChannelResponseSchema
from shared.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from shared.schemas.slot import SlotCreate, SlotFilter, SlotResponse
from shared.schemas.tenant import BaseTenantModel

__all__ = [
    "BaseTenantModel",
    "ChannelCreate",
    "ChannelUpdate",
    "ChannelResponseSchema",
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse",
    "SlotFilter",
    "SlotCreate",
    "SlotResponse",
]
