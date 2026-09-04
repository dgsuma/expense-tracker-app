"""Analytics service: summaries, category breakdowns, trends, budget-vs-actual."""

import calendar
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics import AnalyticsRepository
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository
from app.schemas.analytics import (
    CategoryTotalItem,
    CategoryTotalsResponse,
    SummaryResponse,
    TrendPoint,
    TrendsResponse,
)
from app.schemas.budget import BudgetVsActualItem


def _period_bounds(period: str, ref: date) -> tuple[date, date]:
    """Return [start, end] for the period containing the reference date."""
    if period == "daily":
        return ref, ref
    if period == "weekly":
        start = ref - timedelta(days=ref.weekday())  # Monday
        return start, start + timedelta(days=6)
    if period == "monthly":
        last = calendar.monthrange(ref.year, ref.month)[1]
        return date(ref.year, ref.month, 1), date(ref.year, ref.month, last)
    if period == "annual":
        return date(ref.year, 1, 1), date(ref.year, 12, 31)
    raise ValueError(f"Unknown period: {period}")


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AnalyticsRepository(session)
        self.budgets = BudgetRepository(session)
        self.categories = CategoryRepository(session)

    async def summary(
        self, *, user_id: UUID, period: str, ref: date, currency: str
    ) -> SummaryResponse:
        start, end = _period_bounds(period, ref)
        total, count = await self.repo.summary(user_id, start, end)
        average = (total / count) if count else Decimal(0)
        return SummaryResponse(
            period=period,
            period_start=start,
            period_end=end,
            total=total,
            count=count,
            average=average.quantize(Decimal("0.01")),
            currency=currency,
        )

    async def by_category(
        self, *, user_id: UUID, date_from: date, date_to: date, currency: str
    ) -> CategoryTotalsResponse:
        rows = await self.repo.by_category(user_id, date_from, date_to)
        grand_total = sum((r[2] for r in rows), Decimal(0))
        items = [
            CategoryTotalItem(
                category_id=row[0],
                category_name=row[1],
                total=row[2],
                count=row[3],
                percent=round(float(row[2] / grand_total * 100), 2) if grand_total else 0.0,
            )
            for row in rows
        ]
        return CategoryTotalsResponse(
            period_start=date_from,
            period_end=date_to,
            total=grand_total,
            currency=currency,
            items=items,
        )

    async def trends(
        self, *, user_id: UUID, date_from: date, date_to: date, granularity: str, currency: str
    ) -> TrendsResponse:
        rows = await self.repo.trends(user_id, date_from, date_to, granularity)
        return TrendsResponse(
            granularity=granularity,
            period_start=date_from,
            period_end=date_to,
            currency=currency,
            points=[TrendPoint(bucket=r[0], total=r[1], count=r[2]) for r in rows],
        )

    async def budget_vs_actual(self, *, user_id: UUID, ref: date) -> list[BudgetVsActualItem]:
        budgets = await self.budgets.list_for_user(user_id)
        # Category names for display
        cats = await self.categories.list_for_user(user_id)
        cat_names = {c.id: c.name for c in cats}

        results: list[BudgetVsActualItem] = []
        for budget in budgets:
            start, end = _period_bounds(budget.period, ref)
            actual = await self.repo.total_for_period(user_id, start, end, budget.category_id)
            remaining = budget.amount - actual
            percent = round(float(actual / budget.amount * 100), 2) if budget.amount else 0.0
            results.append(
                BudgetVsActualItem(
                    budget_id=budget.id,
                    category_id=budget.category_id,
                    category_name=cat_names.get(budget.category_id)
                    if budget.category_id
                    else "Overall",
                    budget_amount=budget.amount,
                    actual_amount=actual,
                    remaining=remaining,
                    percent_used=percent,
                    period=budget.period,
                    period_start=start,
                    period_end=end,
                )
            )
        return results
