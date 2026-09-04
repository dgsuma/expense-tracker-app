"""Budget data access — strictly per-user."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget


class BudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Budget]:
        result = await self.session.execute(
            select(Budget).where(Budget.user_id == user_id).order_by(Budget.start_date.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(self, budget_id: UUID, user_id: UUID) -> Budget | None:
        result = await self.session.execute(
            select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: UUID, **fields) -> Budget:
        budget = Budget(user_id=user_id, **fields)
        self.session.add(budget)
        await self.session.flush()
        return budget
