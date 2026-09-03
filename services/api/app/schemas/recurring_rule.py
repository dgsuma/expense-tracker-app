"""Recurring rule schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RecurringRuleCreateRequest(BaseModel):
    category_id: UUID
    payment_method_id: UUID | None = None
    amount: Decimal = Field(gt=0, le=999999999999.99)
    currency: str = Field(min_length=3, max_length=3)
    description: str = Field(min_length=1, max_length=200)
    frequency: str = Field(pattern="^(daily|weekly|monthly|annual)$")
    next_run_date: date


class RecurringRuleUpdateRequest(BaseModel):
    category_id: UUID | None = None
    payment_method_id: UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, le=999999999999.99)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    description: str | None = Field(default=None, min_length=1, max_length=200)
    frequency: str | None = Field(default=None, pattern="^(daily|weekly|monthly|annual)$")
    next_run_date: date | None = None
    is_active: bool | None = None


class RecurringRuleResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    payment_method_id: UUID | None
    amount: Decimal
    currency: str
    description: str
    frequency: str
    next_run_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
