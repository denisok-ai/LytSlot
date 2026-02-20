"""
@file: test_rls.py
@description: Интеграционные тесты RLS: тенант видит только свои заказы.
@dependencies: pytest, tests.conftest
@created: 2025-02-20
"""

from fastapi.testclient import TestClient


def test_rls_tenant_a_does_not_see_tenant_b_orders(
    client: TestClient,
    token_a: str,
    token_b: str,
    channel_a,
    channel_b,
    slot_a,
    slot_b,
):
    """Тенант A не видит заказы тенанта B в списке."""
    # Тенант B создаёт заказ
    r_b = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "channel_id": str(channel_b.id),
            "slot_id": str(slot_b.id),
            "content": {"text": "Order of B"},
        },
    )
    assert r_b.status_code == 201
    order_b_id = r_b.json()["id"]

    # Тенант A запрашивает список — заказа B в нём быть не должно
    r_a = client.get("/api/orders", headers={"Authorization": f"Bearer {token_a}"})
    assert r_a.status_code == 200
    orders_a = r_a.json()
    ids_a = [o["id"] for o in orders_a]
    assert order_b_id not in ids_a


def test_rls_tenant_b_does_not_see_tenant_a_orders(
    client: TestClient,
    token_a: str,
    token_b: str,
    channel_a,
    channel_b,
    slot_a,
    slot_b,
):
    """Тенант B не видит заказы тенанта A в списке."""
    # Тенант A создаёт заказ
    r_a = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "channel_id": str(channel_a.id),
            "slot_id": str(slot_a.id),
            "content": {"text": "Order of A"},
        },
    )
    assert r_a.status_code == 201
    order_a_id = r_a.json()["id"]

    # Тенант B запрашивает список — заказа A в нём быть не должно
    r_b = client.get("/api/orders", headers={"Authorization": f"Bearer {token_b}"})
    assert r_b.status_code == 200
    orders_b = r_b.json()
    ids_b = [o["id"] for o in orders_b]
    assert order_a_id not in ids_b


def test_rls_get_order_by_id_returns_404_for_other_tenant(
    client: TestClient,
    token_a: str,
    token_b: str,
    channel_b,
    slot_b,
):
    """GET /orders/{id} возвращает 404, если заказ принадлежит другому тенанту."""
    # B создаёт заказ
    r_b = client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "channel_id": str(channel_b.id),
            "slot_id": str(slot_b.id),
            "content": {"text": "B order"},
        },
    )
    assert r_b.status_code == 201
    order_b_id = r_b.json()["id"]

    # A пытается получить заказ B по ID — должен получить 404
    r_a = client.get(
        f"/api/orders/{order_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_a.status_code == 404
