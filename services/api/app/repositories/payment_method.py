"""Payment method data access — strictly per-user."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_method import PaymentMethod


class PaymentMethodRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[PaymentMethod]:
        result = await self.session.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.name)
        )
        return list(result.scalars().all())

    async def get_for_user(self, pm_id: UUID, user_id: UUID) -> PaymentMethod | None:
        result = await self.session.execute(
            select(PaymentMethod).where(PaymentMethod.id == pm_id, PaymentMethod.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: UUID, name: str, type: str) -> PaymentMethod:
        pm = PaymentMethod(user_id=user_id, name=name, type=type)
        self.session.add(pm)
        await self.session.flush()
        return pm
