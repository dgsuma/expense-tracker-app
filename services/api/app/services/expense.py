"""Expense service."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.expense import Expense
from app.repositories.category import CategoryRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.payment_method import PaymentMethodRepository


class ExpenseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ExpenseRepository(session)
        self.categories = CategoryRepository(session)
        self.payment_methods = PaymentMethodRepository(session)

    async def list(self, user_id: UUID, **filters) -> tuple[list[Expense], int]:
        return await self.repo.list_for_user(user_id, **filters)

    async def get(self, *, expense_id: UUID, user_id: UUID) -> Expense:
        expense = await self.repo.get_for_user(expense_id, user_id)
        if expense is None:
            raise NotFoundError("Expense not found.")
        return expense

    async def create(self, *, user_id: UUID, **fields) -> Expense:
        await self._validate_references(
            user_id, fields.get("category_id"), fields.get("payment_method_id")
        )
        expense = await self.repo.create(user_id=user_id, **fields)
        await self.session.commit()
        return expense

    async def update(self, *, expense_id: UUID, user_id: UUID, **fields) -> Expense:
        expense = await self.get(expense_id=expense_id, user_id=user_id)
        # Only validate references that are being changed.
        new_category = fields.get("category_id")
        new_pm = fields.get("payment_method_id")
        if new_category is not None or new_pm is not None:
            await self._validate_references(
                user_id,
                new_category if new_category is not None else expense.category_id,
                new_pm if new_pm is not None else expense.payment_method_id,
            )
        for key, value in fields.items():
            if value is not None:
                setattr(expense, key, value)
        await self.session.commit()
        return expense

    async def delete(self, *, expense_id: UUID, user_id: UUID) -> None:
        expense = await self.get(expense_id=expense_id, user_id=user_id)
        expense.deleted_at = datetime.now(UTC)
        await self.session.commit()

    async def restore(self, *, expense_id: UUID, user_id: UUID) -> Expense:
        result = await self.repo._base_query(user_id, include_deleted=True).where(
            Expense.id == expense_id
        )
        expense = (await self.session.execute(result)).scalar_one_or_none()
        if expense is None:
            raise NotFoundError("Expense not found.")
        expense.deleted_at = None
        await self.session.commit()
        return expense

    async def _validate_references(
        self, user_id: UUID, category_id: UUID | None, payment_method_id: UUID | None
    ) -> None:
        if category_id is not None:
            if await self.categories.get_for_user(category_id, user_id) is None:
                raise NotFoundError("Category not found.")
        if payment_method_id is not None:
            if await self.payment_methods.get_for_user(payment_method_id, user_id) is None:
                raise NotFoundError("Payment method not found.")
