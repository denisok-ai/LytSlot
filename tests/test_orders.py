"""
@file: test_orders.py
@description: Интеграционные тесты: создание заказа, список заказов.
@dependencies: pytest, tests.conftest
@created: 2025-02-20
"""

from fastapi.testclient import TestClient


def test_create_order(
    client: TestClient,
    token_a: str,
    channel_a,
    slot_a,
):
    """Создание заказа по API возвращает 201 и данные заказа."""
    r = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "channel_id": str(channel_a.id),
            "slot_id": str(slot_a.id),
            "content": {"text": "Test ad"},
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["status"] == "draft"
    assert data["channel_id"] == str(channel_a.id)
    assert data["slot_id"] == str(slot_a.id)
    assert data["content"] == {"text": "Test ad"}
    assert "id" in data


def test_list_orders_after_create(
    client: TestClient,
    token_a: str,
    channel_a,
    slot_a,
):
    """После создания заказа он попадает в список заказов тенанта."""
    create = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "channel_id": str(channel_a.id),
            "slot_id": str(slot_a.id),
            "content": {"text": "List test"},
        },
    )
    assert create.status_code == 201
    order_id = create.json()["id"]

    r = client.get("/api/orders", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    orders = r.json()
    ids = [o["id"] for o in orders]
    assert order_id in ids
