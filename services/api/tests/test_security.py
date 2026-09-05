"""Unit tests for the security layer (no database required)."""

import time
from uuid import uuid4

import jwt as pyjwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        hashed = hash_password("Str0ng!Passw0rd")
        assert verify_password("Str0ng!Passw0rd", hashed) is True

    def test_wrong_password_rejected(self) -> None:
        hashed = hash_password("Str0ng!Passw0rd")
        assert verify_password("WrongPass123", hashed) is False

    def test_hashes_are_unique_per_call(self) -> None:
        # Argon2 uses a random salt → same password hashes differently each time.
        assert hash_password("same") != hash_password("same")

    def test_hash_is_argon2(self) -> None:
        assert hash_password("x").startswith("$argon2")


class TestAccessTokens:
    def test_create_and_decode(self) -> None:
        user_id = uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_expiry_is_set(self) -> None:
        settings = get_settings()
        token = create_access_token(uuid4(), "user")
        payload = decode_access_token(token)
        assert payload["exp"] - payload["iat"] == settings.access_token_ttl_minutes * 60

    def test_tampered_token_rejected(self) -> None:
        token = create_access_token(uuid4(), "user")
        with pytest.raises(pyjwt.PyJWTError):
            decode_access_token(token + "tampered")

    def test_wrong_secret_rejected(self) -> None:
        token = create_access_token(uuid4(), "user")
        with pytest.raises(pyjwt.PyJWTError):
            pyjwt.decode(token, "wrong-secret", algorithms=["HS256"])

    def test_expired_token_rejected(self) -> None:
        settings = get_settings()
        user_id = uuid4()
        # Craft an already-expired token directly.
        now = int(time.time())
        expired = pyjwt.encode(
            {
                "sub": str(user_id),
                "role": "user",
                "type": "access",
                "iat": now - 1000,
                "exp": now - 1,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(expired)


class TestRefreshTokens:
    def test_tokens_are_unique(self) -> None:
        assert generate_refresh_token() != generate_refresh_token()

    def test_hash_is_deterministic(self) -> None:
        token = generate_refresh_token()
        assert hash_refresh_token(token) == hash_refresh_token(token)

    def test_hash_is_sha256_hex(self) -> None:
        digest = hash_refresh_token("anything")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_different_tokens_different_hashes(self) -> None:
        assert hash_refresh_token(generate_refresh_token()) != hash_refresh_token(
            generate_refresh_token()
        )
