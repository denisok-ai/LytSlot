"""
@file: test_health.py
@description: Тесты эндпоинтов /health и /ready.
@dependencies: pytest, tests.conftest
@created: 2025-02-20
"""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    """GET /health возвращает 200 и status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_returns_ready_when_db_ok(client: TestClient):
    """GET /ready возвращает 200 и status ready при доступной БД."""
    r = client.get("/ready")
    # БД в тестах должна быть доступна
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"


def test_request_id_in_response(client: TestClient):
    """Ответ содержит заголовок X-Request-Id."""
    r = client.get("/health")
    assert r.status_code == 200
    assert "x-request-id" in r.headers or "X-Request-Id" in r.headers
