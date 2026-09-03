"""Authentication service: register, login, refresh rotation, logout.

Refresh token rotation: every successful refresh revokes the presented token
and issues a new one. If a *revoked* token is presented, that indicates theft
(a legitimate client would have used its replacement) — the entire token
family for that user is revoked as a defensive measure.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tokens = RefreshTokenRepository(session)

    async def register(
        self, *, email: str, password: str, display_name: str, default_currency: str
    ) -> User:
        if await self.users.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists.")
        user = await self.users.create(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            default_currency=default_currency,
        )
        await self.session.commit()
        return user

    async def login(self, *, email: str, password: str) -> TokenResponse:
        user = await self.users.get_by_email(email)
        # Uniform failure — do not reveal whether the email exists.
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled.")
        return await self._issue_token_pair(user)

    async def refresh(self, *, refresh_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(refresh_token)
        stored = await self.tokens.get_by_hash(token_hash)

        if stored is None:
            raise UnauthorizedError("Invalid refresh token.")

        if stored.revoked_at is not None:
            # Reuse of a rotated token → possible theft. Revoke the whole family.
            await self.tokens.revoke_all_for_user(stored.user_id)
            await self.session.commit()
            raise UnauthorizedError("Refresh token reuse detected. Please log in again.")

        if stored.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired.")

        user = await self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Account is disabled.")

        # Rotate: revoke the presented token, issue a new pair.
        await self.tokens.revoke(stored)
        response = await self._issue_token_pair(user)
        await self.session.commit()
        return response

    async def logout(self, *, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored = await self.tokens.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            await self.tokens.revoke(stored)
            await self.session.commit()

    async def change_password(self, *, user_id: UUID, current: str, new: str) -> None:
        user = await self.users.get_by_id(user_id)
        if user is None or not verify_password(current, user.password_hash):
            raise UnauthorizedError("Current password is incorrect.")
        user.password_hash = hash_password(new)
        await self.tokens.revoke_all_for_user(user_id)
        await self.session.commit()

    async def _issue_token_pair(self, user: User) -> TokenResponse:
        settings = get_settings()
        access_token = create_access_token(user.id, user.role)
        refresh_token = generate_refresh_token()
        await self.tokens.create(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days),
        )
        await self.session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_ttl_minutes * 60,
        )
