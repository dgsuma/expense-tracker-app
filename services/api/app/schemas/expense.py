"""Expense schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    category_id: UUID
    payment_method_id: UUID | None = None
    amount: Decimal = Field(gt=0, le=999999999999.99)
    currency: str = Field(min_length=3, max_length=3)
    expense_date: date
    description: str = Field(min_length=1, max_length=200)
    notes: str | None = None


class ExpenseUpdateRequest(BaseModel):
    category_id: UUID | None = None
    payment_method_id: UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, le=999999999999.99)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    expense_date: date | None = None
    description: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None


class ExpenseResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    payment_method_id: UUID | None
    recurring_rule_id: UUID | None
    amount: Decimal
    currency: str
    expense_date: date
    description: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = {"from_attributes": True}
