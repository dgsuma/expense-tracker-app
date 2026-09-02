"""Phase 1 acceptance tests: ops endpoints, error shape, request context."""

from unittest.mock import patch

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_when_database_up(client: AsyncClient) -> None:
    with patch("app.api.ops.ping_database", return_value=True):
        response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


async def test_ready_when_database_down(client: AsyncClient) -> None:
    with patch("app.api.ops.ping_database", return_value=False):
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "down"}


async def test_unknown_route_returns_rfc7807_problem(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["instance"] == "/api/v1/does-not-exist"
    assert body["request_id"] is not None


async def test_request_id_echoed_and_generated(client: AsyncClient) -> None:
    # Client-supplied ID is echoed
    response = await client.get("/health", headers={"X-Request-ID": "req-123"})
    assert response.headers["X-Request-ID"] == "req-123"
    # Otherwise one is generated
    response = await client.get("/health")
    assert "X-Request-ID" in response.headers
