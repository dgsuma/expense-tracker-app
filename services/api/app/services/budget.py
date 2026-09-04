"""Budget service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.budget import Budget
from app.repositories.budget import BudgetRepository
from app.repositories.category import CategoryRepository


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BudgetRepository(session)
        self.categories = CategoryRepository(session)

    async def list(self, user_id: UUID) -> list[Budget]:
        return await self.repo.list_for_user(user_id)

    async def create(self, *, user_id: UUID, **fields) -> Budget:
        category_id = fields.get("category_id")
        if category_id is not None:
            if await self.categories.get_for_user(category_id, user_id) is None:
                raise NotFoundError("Category not found.")
        budget = await self.repo.create(user_id=user_id, **fields)
        await self.session.commit()
        return budget

    async def update(self, *, budget_id: UUID, user_id: UUID, **fields) -> Budget:
        budget = await self.repo.get_for_user(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget not found.")
        for key, value in fields.items():
            if value is not None:
                setattr(budget, key, value)
        await self.session.commit()
        return budget

    async def delete(self, *, budget_id: UUID, user_id: UUID) -> None:
        budget = await self.repo.get_for_user(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget not found.")
        await self.session.delete(budget)
        await self.session.commit()
