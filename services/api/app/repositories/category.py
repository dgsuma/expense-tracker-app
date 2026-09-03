"""Category data access. Users see system defaults (user_id NULL) plus their own."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Category]:
        """System defaults + the user's own categories, ordered for tree building."""
        result = await self.session.execute(
            select(Category)
            .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
            .order_by(Category.parent_id.isnot(None), Category.name)
        )
        return list(result.scalars().all())

    async def get_for_user(self, category_id: UUID, user_id: UUID) -> Category | None:
        """A category the user can use: their own, or a system default."""
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                or_(Category.user_id.is_(None), Category.user_id == user_id),
            )
        )
        return result.scalar_one_or_none()

    async def get_owned(self, category_id: UUID, user_id: UUID) -> Category | None:
        """A category the user owns (can edit/delete). System defaults are excluded."""
        result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, user_id: UUID, name: str, parent_id: UUID | None, kind: str
    ) -> Category:
        category = Category(user_id=user_id, name=name, parent_id=parent_id, kind=kind)
        self.session.add(category)
        await self.session.flush()
        return category

    async def has_expenses(self, category_id: UUID) -> bool:
        from app.models.expense import Expense

        result = await self.session.execute(
            select(Expense.id).where(Expense.category_id == category_id).limit(1)
        )
        return result.scalar_one_or_none() is not None
