"""Phase 3 acceptance tests: authentication flows.

These tests run against the real database (the compose stack must be up).
Each test registers a unique user so they are independent and idempotent.
"""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1"


def _unique_user() -> dict:
    suffix = uuid.uuid4().hex[:8]
    return {
        "email": f"user-{suffix}@example.com",
        "password": "Str0ng!Passw0rd",
        "display_name": "Test User",
        "default_currency": "EUR",
    }


async def _register(client: AsyncClient, user: dict) -> None:
    response = await client.post(f"{BASE}/auth/register", json=user)
    assert response.status_code == 201, response.text


async def _login(client: AsyncClient, user: dict) -> dict:
    response = await client.post(
        f"{BASE}/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_register_creates_user(client: AsyncClient) -> None:
    user = _unique_user()
    response = await client.post(f"{BASE}/auth/register", json=user)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == user["email"]
    assert body["display_name"] == "Test User"
    assert "password" not in body and "password_hash" not in body


async def test_register_duplicate_email_conflict(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    response = await client.post(f"{BASE}/auth/register", json=user)
    assert response.status_code == 409


async def test_register_weak_password_rejected(client: AsyncClient) -> None:
    user = _unique_user()
    user["password"] = "short"
    response = await client.post(f"{BASE}/auth/register", json=user)
    assert response.status_code == 422


async def test_login_returns_token_pair(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    tokens = await _login(client, user)
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    response = await client.post(
        f"{BASE}/auth/login", json={"email": user["email"], "password": "WrongPass123"}
    )
    assert response.status_code == 401


async def test_me_with_valid_token(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    tokens = await _login(client, user)
    response = await client.get(
        f"{BASE}/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == user["email"]


async def test_me_without_token(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/users/me")
    assert response.status_code == 401


async def test_refresh_rotates_tokens(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    tokens = await _login(client, user)
    response = await client.post(
        f"{BASE}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert new_tokens["access_token"] != tokens["access_token"]


async def test_refresh_reuse_revokes_family(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    tokens = await _login(client, user)
    old_refresh = tokens["refresh_token"]

    # First refresh succeeds and rotates
    first = await client.post(f"{BASE}/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200
    rotated_refresh = first.json()["refresh_token"]

    # Reusing the OLD (now revoked) token triggers theft detection
    reuse = await client.post(f"{BASE}/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401

    # The rotated token is also revoked (whole family invalidated)
    family = await client.post(f"{BASE}/auth/refresh", json={"refresh_token": rotated_refresh})
    assert family.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    user = _unique_user()
    await _register(client, user)
    tokens = await _login(client, user)
    response = await client.post(
        f"{BASE}/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 204
    # Subsequent refresh with the logged-out token fails
    refresh = await client.post(
        f"{BASE}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401
