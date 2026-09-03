"""Password hashing, JWT access tokens, and refresh token helpers.

- Passwords: Argon2id (memory-hard, per-user salt) via argon2-cffi.
- Access tokens: short-lived JWT (HS256), carry user id + role.
- Refresh tokens: opaque random strings; only their SHA-256 hash is stored.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import get_settings

_password_hasher = PasswordHasher()  # Argon2id with sane defaults


# --- Passwords ---------------------------------------------------------------


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain)
    except (VerifyMismatchError, VerificationError):
        return False


# --- Access tokens (JWT) -----------------------------------------------------


def create_access_token(user_id: UUID, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token. Raises jwt.PyJWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# --- Refresh tokens (opaque) -------------------------------------------------


def generate_refresh_token() -> str:
    """A new opaque refresh token (URL-safe, 256 bits of entropy)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex digest — this is what gets stored, never the raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
