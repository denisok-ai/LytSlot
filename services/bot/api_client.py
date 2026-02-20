"""
@file: api_client.py
@description: HTTP client for FastAPI (auth, channels, slots, orders).
@dependencies: httpx
@created: 2025-02-19
"""

from datetime import datetime
from uuid import UUID

import httpx

from services.bot.config import settings


async def get_token(telegram_id: int) -> str | None:
    """Получить JWT по telegram_id (POST /api/auth/dev-login). Требует ENABLE_DEV_LOGIN=true."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.api_base_url}/api/auth/dev-login",
            json={"telegram_id": telegram_id},
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("access_token")


async def get_channels(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.api_base_url}/api/channels",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()


async def get_slots(
    token: str,
    channel_id: UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        params = {"channel_id": str(channel_id)}
        if date_from is not None:
            params["date_from"] = date_from.isoformat()
        if date_to is not None:
            params["date_to"] = date_to.isoformat()
        r = await client.get(
            f"{settings.api_base_url}/api/slots",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        r.raise_for_status()
        return r.json()


async def create_order(
    token: str, channel_id: UUID, slot_id: UUID, content: dict, erid: str | None = None
) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.api_base_url}/api/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "channel_id": str(channel_id),
                "slot_id": str(slot_id),
                "content": content,
                "erid": erid,
            },
        )
        r.raise_for_status()
        return r.json()
