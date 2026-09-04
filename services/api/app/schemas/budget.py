"""Budget schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetCreateRequest(BaseModel):
    category_id: UUID | None = None  # NULL = overall budget
    amount: Decimal = Field(gt=0, le=999999999999.99)
    period: str = Field(pattern="^(weekly|monthly|annual)$")
    start_date: date


class BudgetUpdateRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, le=999999999999.99)
    period: str | None = Field(default=None, pattern="^(weekly|monthly|annual)$")
    start_date: date | None = None


class BudgetResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID | None
    amount: Decimal
    period: str
    start_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetVsActualItem(BaseModel):
    budget_id: UUID
    category_id: UUID | None
    category_name: str | None
    budget_amount: Decimal
    actual_amount: Decimal
    remaining: Decimal
    percent_used: float
    period: str
    period_start: date
    period_end: date
