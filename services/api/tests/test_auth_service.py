"""Unit tests for AuthService with mocked repositories (no database)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password
from app.services.auth import AuthService


def _make_user(**overrides) -> MagicMock:
    user = MagicMock()
    user.id = uuid4()
    user.email = "user@example.com"
    user.password_hash = hash_password("Str0ng!Passw0rd")
    user.display_name = "User"
    user.role = "user"
    user.is_active = True
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def _service() -> AuthService:
    session = AsyncMock()
    service = AuthService(session)
    service.users = AsyncMock()
    service.tokens = AsyncMock()
    return service


class TestRegister:
    async def test_register_success(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = None
        service.users.create.return_value = _make_user()
        user = await service.register(
            email="new@example.com",
            password="Str0ng!Passw0rd",
            display_name="New",
            default_currency="EUR",
        )
        assert user is not None
        service.users.create.assert_awaited_once()

    async def test_register_duplicate_email(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = _make_user()
        with pytest.raises(ConflictError):
            await service.register(
                email="dup@example.com",
                password="Str0ng!Passw0rd",
                display_name="Dup",
                default_currency="EUR",
            )


class TestLogin:
    async def test_login_success(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = _make_user()
        result = await service.login(email="user@example.com", password="Str0ng!Passw0rd")
        assert result.access_token
        assert result.refresh_token
        assert result.expires_in > 0

    async def test_login_wrong_password(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = _make_user()
        with pytest.raises(UnauthorizedError):
            await service.login(email="user@example.com", password="WrongPass123")

    async def test_login_unknown_email(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = None
        with pytest.raises(UnauthorizedError):
            await service.login(email="ghost@example.com", password="Str0ng!Passw0rd")

    async def test_login_inactive_account(self) -> None:
        service = _service()
        service.users.get_by_email.return_value = _make_user(is_active=False)
        with pytest.raises(UnauthorizedError):
            await service.login(email="user@example.com", password="Str0ng!Passw0rd")


class TestRefresh:
    async def test_refresh_rotates(self) -> None:
        service = _service()
        user = _make_user()
        stored = MagicMock()
        stored.user_id = user.id
        stored.revoked_at = None
        stored.expires_at = datetime.now(UTC) + timedelta(days=30)
        service.tokens.get_by_hash.return_value = stored
        service.users.get_by_id.return_value = user

        result = await service.refresh(refresh_token="old-token")
        assert result.refresh_token != "old-token"
        service.tokens.revoke.assert_awaited_once_with(stored)

    async def test_refresh_unknown_token(self) -> None:
        service = _service()
        service.tokens.get_by_hash.return_value = None
        with pytest.raises(UnauthorizedError):
            await service.refresh(refresh_token="ghost")

    async def test_refresh_reuse_revokes_family(self) -> None:
        service = _service()
        stored = MagicMock()
        stored.user_id = uuid4()
        stored.revoked_at = datetime.now(UTC)  # already revoked
        service.tokens.get_by_hash.return_value = stored

        with pytest.raises(UnauthorizedError, match="reuse"):
            await service.refresh(refresh_token="reused")
        service.tokens.revoke_all_for_user.assert_awaited_once_with(stored.user_id)

    async def test_refresh_expired(self) -> None:
        service = _service()
        stored = MagicMock()
        stored.revoked_at = None
        stored.expires_at = datetime.now(UTC) - timedelta(days=1)  # expired
        service.tokens.get_by_hash.return_value = stored
        with pytest.raises(UnauthorizedError, match="expired"):
            await service.refresh(refresh_token="expired-token")


class TestLogout:
    async def test_logout_revokes(self) -> None:
        service = _service()
        stored = MagicMock()
        stored.revoked_at = None
        service.tokens.get_by_hash.return_value = stored
        await service.logout(refresh_token="token")
        service.tokens.revoke.assert_awaited_once_with(stored)

    async def test_logout_unknown_token_is_noop(self) -> None:
        service = _service()
        service.tokens.get_by_hash.return_value = None
        await service.logout(refresh_token="ghost")  # should not raise
        service.tokens.revoke.assert_not_awaited()


class TestChangePassword:
    async def test_change_password_success(self) -> None:
        service = _service()
        user = _make_user()
        service.users.get_by_id.return_value = user
        await service.change_password(
            user_id=user.id, current="Str0ng!Passw0rd", new="N3w!Passw0rdXYZ"
        )
        service.tokens.revoke_all_for_user.assert_awaited_once_with(user.id)

    async def test_change_password_wrong_current(self) -> None:
        service = _service()
        service.users.get_by_id.return_value = _make_user()
        with pytest.raises(UnauthorizedError):
            await service.change_password(
                user_id=uuid4(), current="WrongCurrent123", new="N3w!Passw0rdXYZ"
            )
