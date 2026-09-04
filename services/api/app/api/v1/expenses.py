"""Expense endpoints with search, filtering, pagination, and CSV export."""

import csv
import io
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.expense import ExpenseCreateRequest, ExpenseResponse, ExpenseUpdateRequest
from app.services.expense import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
async def list_expenses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: UUID | None = None,
    payment_method_id: UUID | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    search: str | None = None,
    sort: str = "-expense_date",
) -> PaginatedResponse[ExpenseResponse]:
    expenses, total = await ExpenseService(session).list(
        current_user.id,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        sort=sort,
    )
    return PaginatedResponse(
        items=[ExpenseResponse.model_validate(e) for e in expenses],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    body: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await ExpenseService(session).create(user_id=current_user.id, **body.model_dump())
    return ExpenseResponse.model_validate(expense)


@router.get("/export")
async def export_expenses_csv(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: UUID | None = None,
    search: str | None = None,
) -> StreamingResponse:
    """Export the filtered expense set as CSV (Excel-compatible, UTF-8 BOM)."""
    expenses, _ = await ExpenseService(session).list(
        current_user.id,
        page=1,
        page_size=10000,  # export cap
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        search=search,
        sort="-expense_date",
    )

    buffer = io.StringIO()
    buffer.write("﻿")  # UTF-8 BOM so Excel opens it correctly
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Description", "Amount", "Currency", "Notes", "Created"])
    for e in expenses:
        writer.writerow(
            [
                e.expense_date.isoformat(),
                e.description,
                str(e.amount),
                e.currency,
                e.notes or "",
                e.created_at.isoformat(),
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await ExpenseService(session).get(expense_id=expense_id, user_id=current_user.id)
    return ExpenseResponse.model_validate(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: UUID,
    body: ExpenseUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await ExpenseService(session).update(
        expense_id=expense_id,
        user_id=current_user.id,
        **body.model_dump(exclude_unset=True),
    )
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await ExpenseService(session).delete(expense_id=expense_id, user_id=current_user.id)


@router.post("/{expense_id}/restore", response_model=ExpenseResponse)
async def restore_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    expense = await ExpenseService(session).restore(expense_id=expense_id, user_id=current_user.id)
    return ExpenseResponse.model_validate(expense)
