"""Unit tests for schema validation (no database required)."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.expense import ExpenseCreateRequest


class TestRegisterRequest:
    def _valid(self) -> dict:
        return {
            "email": "user@example.com",
            "password": "Str0ng!Passw0rd",
            "display_name": "User",
            "default_currency": "eur",
        }

    def test_valid(self) -> None:
        req = RegisterRequest(**self._valid())
        assert req.email == "user@example.com"
        assert req.default_currency == "EUR"  # uppercased by validator

    def test_short_password_rejected(self) -> None:
        data = self._valid()
        data["password"] = "Short1"
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_password_needs_uppercase(self) -> None:
        data = self._valid()
        data["password"] = "alllowercase123"
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_password_needs_digit(self) -> None:
        data = self._valid()
        data["password"] = "NoDigitsHereABC"
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_invalid_email_rejected(self) -> None:
        data = self._valid()
        data["email"] = "not-an-email"
        with pytest.raises(ValidationError):
            RegisterRequest(**data)


class TestExpenseCreateRequest:
    def _valid(self) -> dict:
        return {
            "category_id": "123e4567-e89b-12d3-a456-426614174000",
            "amount": "42.50",
            "currency": "EUR",
            "expense_date": "2026-09-03",
            "description": "Lunch",
        }

    def test_valid(self) -> None:
        req = ExpenseCreateRequest(**self._valid())
        assert str(req.amount) == "42.50"

    def test_zero_amount_rejected(self) -> None:
        data = self._valid()
        data["amount"] = "0"
        with pytest.raises(ValidationError):
            ExpenseCreateRequest(**data)

    def test_negative_amount_rejected(self) -> None:
        data = self._valid()
        data["amount"] = "-5"
        with pytest.raises(ValidationError):
            ExpenseCreateRequest(**data)

    def test_empty_description_rejected(self) -> None:
        data = self._valid()
        data["description"] = ""
        with pytest.raises(ValidationError):
            ExpenseCreateRequest(**data)
