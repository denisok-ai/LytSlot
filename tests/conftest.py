"""
@file: conftest.py
@description: Pytest fixtures for API integration tests (client, DB, tenants, JWT).
@dependencies: pytest, fastapi.testclient, db, services.api
@created: 2025-02-20
"""

import os
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Включаем dev-login и отключаем Celery для тестов (до импорта app)
os.environ.setdefault("ENABLE_DEV_LOGIN", "true")
os.environ.setdefault("CELERY_BROKER_URL", "")

from db.database import SessionLocal
from db.models import Channel, Slot, Tenant
from services.api.main import app


@pytest.fixture(scope="session")
def client():
    """Тестовый HTTP-клиент для API."""
    return TestClient(app)


@pytest.fixture
def db():
    """Сессия БД для подготовки данных. После теста откатываем изменения."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def tenant_a(db: Session):
    """Тенант A (telegram_id=9001) для тестов заказов и RLS."""
    t = db.query(Tenant).filter(Tenant.telegram_id == 9001).first()
    if not t:
        t = Tenant(telegram_id=9001, name="Test Tenant A")
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


@pytest.fixture
def tenant_b(db: Session):
    """Тенант B (telegram_id=9002) для тестов RLS."""
    t = db.query(Tenant).filter(Tenant.telegram_id == 9002).first()
    if not t:
        t = Tenant(telegram_id=9002, name="Test Tenant B")
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


@pytest.fixture
def token_a(client: TestClient, tenant_a: Tenant):
    """JWT для tenant_a (через dev-login)."""
    r = client.post("/api/auth/dev-login", json={"telegram_id": tenant_a.telegram_id})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def token_b(client: TestClient, tenant_b: Tenant):
    """JWT для tenant_b (через dev-login)."""
    r = client.post("/api/auth/dev-login", json={"telegram_id": tenant_b.telegram_id})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def channel_a(db: Session, tenant_a: Tenant):
    """Канал тенанта A."""
    ch = db.query(Channel).filter(Channel.tenant_id == tenant_a.id).first()
    if not ch:
        ch = Channel(
            tenant_id=tenant_a.id,
            username="@test_channel_a",
            slot_duration=3600,
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)
    return ch


@pytest.fixture
def slot_a(db: Session, channel_a: Channel):
    """Слот в channel_a."""
    slot = db.query(Slot).filter(Slot.channel_id == channel_a.id).first()
    if not slot:
        slot = Slot(
            channel_id=channel_a.id,
            datetime=datetime.now(UTC),
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
    return slot


@pytest.fixture
def channel_b(db: Session, tenant_b: Tenant):
    """Канал тенанта B."""
    ch = db.query(Channel).filter(Channel.tenant_id == tenant_b.id).first()
    if not ch:
        ch = Channel(
            tenant_id=tenant_b.id,
            username="@test_channel_b",
            slot_duration=3600,
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)
    return ch


@pytest.fixture
def slot_b(db: Session, channel_b: Channel):
    """Слот в channel_b."""
    slot = db.query(Slot).filter(Slot.channel_id == channel_b.id).first()
    if not slot:
        slot = Slot(
            channel_id=channel_b.id,
            datetime=datetime.now(UTC),
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
    return slot
