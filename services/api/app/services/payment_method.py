"""Payment method service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.payment_method import PaymentMethod
from app.repositories.payment_method import PaymentMethodRepository


class PaymentMethodService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PaymentMethodRepository(session)

    async def list(self, user_id: UUID) -> list[PaymentMethod]:
        return await self.repo.list_for_user(user_id)

    async def create(self, *, user_id: UUID, name: str, type: str) -> PaymentMethod:
        pm = await self.repo.create(user_id=user_id, name=name, type=type)
        await self.session.commit()
        return pm

    async def update(
        self,
        *,
        pm_id: UUID,
        user_id: UUID,
        name: str | None,
        type: str | None,
        is_archived: bool | None,
    ) -> PaymentMethod:
        pm = await self.repo.get_for_user(pm_id, user_id)
        if pm is None:
            raise NotFoundError("Payment method not found.")
        if name is not None:
            pm.name = name
        if type is not None:
            pm.type = type
        if is_archived is not None:
            pm.is_archived = is_archived
        await self.session.commit()
        return pm

    async def delete(self, *, pm_id: UUID, user_id: UUID) -> None:
        pm = await self.repo.get_for_user(pm_id, user_id)
        if pm is None:
            raise NotFoundError("Payment method not found.")
        # Archive rather than delete to preserve expense history.
        pm.is_archived = True
        await self.session.commit()
