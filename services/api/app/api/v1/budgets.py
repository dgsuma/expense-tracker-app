"""Budget endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.budget import (
    BudgetCreateRequest,
    BudgetResponse,
    BudgetUpdateRequest,
    BudgetVsActualItem,
)
from app.services.analytics import AnalyticsService
from app.services.budget import BudgetService

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[BudgetResponse]:
    budgets = await BudgetService(session).list(current_user.id)
    return [BudgetResponse.model_validate(b) for b in budgets]


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    body: BudgetCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BudgetResponse:
    budget = await BudgetService(session).create(user_id=current_user.id, **body.model_dump())
    return BudgetResponse.model_validate(budget)


@router.get("/vs-actual", response_model=list[BudgetVsActualItem])
async def budget_vs_actual(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    ref: str | None = Query(
        default=None, description="Reference date (YYYY-MM-DD), defaults to today"
    ),
) -> list[BudgetVsActualItem]:
    ref_date = (
        datetime.now(UTC).date() if ref is None else datetime.strptime(ref, "%Y-%m-%d").date()
    )
    return await AnalyticsService(session).budget_vs_actual(user_id=current_user.id, ref=ref_date)


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    body: BudgetUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BudgetResponse:
    budget = await BudgetService(session).update(
        budget_id=budget_id, user_id=current_user.id, **body.model_dump(exclude_unset=True)
    )
    return BudgetResponse.model_validate(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await BudgetService(session).delete(budget_id=budget_id, user_id=current_user.id)
