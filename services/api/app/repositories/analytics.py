"""Analytics data access — aggregation queries over expenses.

All queries are user-scoped and exclude soft-deleted rows. Amounts are summed
in the user's default currency context (multi-currency conversion is a future
enhancement; for now we aggregate raw amounts and report the user's currency).
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base(self, user_id: UUID, date_from: date, date_to: date):
        return select(Expense).where(
            Expense.user_id == user_id,
            Expense.deleted_at.is_(None),
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to,
        )

    async def summary(self, user_id: UUID, date_from: date, date_to: date) -> tuple[Decimal, int]:
        query = select(
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        ).where(
            Expense.user_id == user_id,
            Expense.deleted_at.is_(None),
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to,
        )
        row = (await self.session.execute(query)).one()
        return Decimal(row[0]), int(row[1])

    async def by_category(
        self, user_id: UUID, date_from: date, date_to: date
    ) -> list[tuple[UUID | None, str, Decimal, int]]:
        """Totals per category (including subcategory rollup to parent name)."""
        parent = Category.__table__.alias("parent_cat")
        query = (
            select(
                func.coalesce(parent.c.id, Category.id).label("group_id"),
                func.coalesce(parent.c.name, Category.name).label("group_name"),
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
                func.count(Expense.id).label("count"),
            )
            .select_from(Expense)
            .join(Category, Expense.category_id == Category.id)
            .outerjoin(parent, Category.parent_id == parent.c.id)
            .where(
                Expense.user_id == user_id,
                Expense.deleted_at.is_(None),
                Expense.expense_date >= date_from,
                Expense.expense_date <= date_to,
            )
            .group_by("group_id", "group_name")
            .order_by(func.sum(Expense.amount).desc())
        )
        result = await self.session.execute(query)
        return [
            (row.group_id, row.group_name, Decimal(row.total), int(row.count)) for row in result
        ]

    async def trends(
        self, user_id: UUID, date_from: date, date_to: date, granularity: str
    ) -> list[tuple[date, Decimal, int]]:
        """Time-series totals bucketed by day/week/month."""
        trunc_map = {"day": "day", "week": "week", "month": "month"}
        trunc = trunc_map.get(granularity, "day")
        bucket = func.date_trunc(trunc, Expense.expense_date).label("bucket")
        query = (
            select(
                bucket,
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(
                Expense.user_id == user_id,
                Expense.deleted_at.is_(None),
                Expense.expense_date >= date_from,
                Expense.expense_date <= date_to,
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        result = await self.session.execute(query)
        return [(row.bucket.date(), Decimal(row.total), int(row.count)) for row in result]

    async def total_for_period(
        self, user_id: UUID, date_from: date, date_to: date, category_id: UUID | None = None
    ) -> Decimal:
        """Total spend in a period, optionally restricted to a category (incl. subcategories)."""
        conditions = [
            Expense.user_id == user_id,
            Expense.deleted_at.is_(None),
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to,
        ]
        if category_id is not None:
            # Match the category itself or any of its subcategories.
            subcategory_ids = select(Category.id).where(Category.parent_id == category_id)
            conditions.append(
                (Expense.category_id == category_id) | (Expense.category_id.in_(subcategory_ids))
            )
        query = select(func.coalesce(func.sum(Expense.amount), 0)).where(*conditions)
        return Decimal((await self.session.execute(query)).scalar_one())
