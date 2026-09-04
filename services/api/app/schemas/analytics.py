"""Analytics schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    period: str
    period_start: date
    period_end: date
    total: Decimal
    count: int
    average: Decimal
    currency: str


class CategoryTotalItem(BaseModel):
    category_id: UUID | None
    category_name: str
    total: Decimal
    count: int
    percent: float


class CategoryTotalsResponse(BaseModel):
    period_start: date
    period_end: date
    total: Decimal
    currency: str
    items: list[CategoryTotalItem]


class TrendPoint(BaseModel):
    bucket: date
    total: Decimal
    count: int


class TrendsResponse(BaseModel):
    granularity: str
    period_start: date
    period_end: date
    currency: str
    points: list[TrendPoint]
