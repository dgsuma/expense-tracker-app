"""Expense data access — strictly per-user, soft-delete aware, with filtering."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense


class ExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self, user_id: UUID, include_deleted: bool = False):
        query = select(Expense).where(Expense.user_id == user_id)
        if not include_deleted:
            query = query.where(Expense.deleted_at.is_(None))
        return query

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 50,
        date_from: date | None = None,
        date_to: date | None = None,
        category_id: UUID | None = None,
        payment_method_id: UUID | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        search: str | None = None,
        sort: str = "-expense_date",
    ) -> tuple[list[Expense], int]:
        query = self._base_query(user_id)

        if date_from is not None:
            query = query.where(Expense.expense_date >= date_from)
        if date_to is not None:
            query = query.where(Expense.expense_date <= date_to)
        if category_id is not None:
            query = query.where(Expense.category_id == category_id)
        if payment_method_id is not None:
            query = query.where(Expense.payment_method_id == payment_method_id)
        if min_amount is not None:
            query = query.where(Expense.amount >= min_amount)
        if max_amount is not None:
            query = query.where(Expense.amount <= max_amount)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(Expense.description.ilike(pattern), Expense.notes.ilike(pattern))
            )

        # Total count for pagination (before limit/offset)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        # Sorting — whitelist to prevent injection
        sortable = {
            "expense_date": Expense.expense_date,
            "amount": Expense.amount,
            "created_at": Expense.created_at,
            "description": Expense.description,
        }
        descending = sort.startswith("-")
        column = sortable.get(sort.lstrip("-"), Expense.expense_date)
        query = query.order_by(column.desc() if descending else column.asc(), Expense.id.desc())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_for_user(self, expense_id: UUID, user_id: UUID) -> Expense | None:
        result = await self.session.execute(
            self._base_query(user_id).where(Expense.id == expense_id)
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: UUID, **fields) -> Expense:
        expense = Expense(user_id=user_id, **fields)
        self.session.add(expense)
        await self.session.flush()
        return expense
