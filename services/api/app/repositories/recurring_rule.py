"""Recurring rule data access — strictly per-user."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring_rule import RecurringRule


class RecurringRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[RecurringRule]:
        result = await self.session.execute(
            select(RecurringRule)
            .where(RecurringRule.user_id == user_id)
            .order_by(RecurringRule.next_run_date)
        )
        return list(result.scalars().all())

    async def get_for_user(self, rule_id: UUID, user_id: UUID) -> RecurringRule | None:
        result = await self.session.execute(
            select(RecurringRule).where(
                RecurringRule.id == rule_id, RecurringRule.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, *, user_id: UUID, **fields) -> RecurringRule:
        rule = RecurringRule(user_id=user_id, **fields)
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def list_due(self, today: date) -> list[RecurringRule]:
        """Active rules due to run (used by the scheduler / run-due endpoint)."""
        result = await self.session.execute(
            select(RecurringRule).where(
                RecurringRule.is_active.is_(True), RecurringRule.next_run_date <= today
            )
        )
        return list(result.scalars().all())
