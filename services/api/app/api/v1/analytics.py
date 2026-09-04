"""Analytics endpoints: summaries, category breakdown, trends."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import CategoryTotalsResponse, SummaryResponse, TrendsResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_date(value: str | None, default: date) -> date:
    return default if value is None else datetime.strptime(value, "%Y-%m-%d").date()


@router.get("/summary", response_model=SummaryResponse)
async def summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    period: str = Query(default="monthly", pattern="^(daily|weekly|monthly|annual)$"),
    date: str | None = Query(default=None, description="Reference date (YYYY-MM-DD)"),
) -> SummaryResponse:
    ref = _parse_date(date, datetime.now(UTC).date())
    return await AnalyticsService(session).summary(
        user_id=current_user.id, period=period, ref=ref, currency=current_user.default_currency
    )


@router.get("/by-category", response_model=CategoryTotalsResponse)
async def by_category(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    date_from: str | None = None,
    date_to: str | None = None,
) -> CategoryTotalsResponse:
    today = datetime.now(UTC).date()
    end = _parse_date(date_to, today)
    start = _parse_date(date_from, today - timedelta(days=30))
    return await AnalyticsService(session).by_category(
        user_id=current_user.id,
        date_from=start,
        date_to=end,
        currency=current_user.default_currency,
    )


@router.get("/trends", response_model=TrendsResponse)
async def trends(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    date_from: str | None = None,
    date_to: str | None = None,
    granularity: str = Query(default="day", pattern="^(day|week|month)$"),
) -> TrendsResponse:
    today = datetime.now(UTC).date()
    end = _parse_date(date_to, today)
    start = _parse_date(date_from, today - timedelta(days=30))
    return await AnalyticsService(session).trends(
        user_id=current_user.id,
        date_from=start,
        date_to=end,
        granularity=granularity,
        currency=current_user.default_currency,
    )
