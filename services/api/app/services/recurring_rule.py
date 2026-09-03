"""Recurring rule service, including generation of due expenses."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.recurring_rule import RecurringRule
from app.repositories.category import CategoryRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.payment_method import PaymentMethodRepository
from app.repositories.recurring_rule import RecurringRuleRepository

_FREQUENCY_DELTA = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),  # approximate; refined in a later phase
    "annual": timedelta(days=365),
}


class RecurringRuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RecurringRuleRepository(session)
        self.expenses = ExpenseRepository(session)
        self.categories = CategoryRepository(session)
        self.payment_methods = PaymentMethodRepository(session)

    async def list(self, user_id: UUID) -> list[RecurringRule]:
        return await self.repo.list_for_user(user_id)

    async def create(self, *, user_id: UUID, **fields) -> RecurringRule:
        if await self.categories.get_for_user(fields["category_id"], user_id) is None:
            raise NotFoundError("Category not found.")
        pm_id = fields.get("payment_method_id")
        if pm_id is not None and await self.payment_methods.get_for_user(pm_id, user_id) is None:
            raise NotFoundError("Payment method not found.")
        rule = await self.repo.create(user_id=user_id, **fields)
        await self.session.commit()
        return rule

    async def update(self, *, rule_id: UUID, user_id: UUID, **fields) -> RecurringRule:
        rule = await self.repo.get_for_user(rule_id, user_id)
        if rule is None:
            raise NotFoundError("Recurring rule not found.")
        for key, value in fields.items():
            if value is not None:
                setattr(rule, key, value)
        await self.session.commit()
        return rule

    async def delete(self, *, rule_id: UUID, user_id: UUID) -> None:
        rule = await self.repo.get_for_user(rule_id, user_id)
        if rule is None:
            raise NotFoundError("Recurring rule not found.")
        rule.is_active = False
        await self.session.commit()

    async def run_due(self, *, today: date) -> int:
        """Generate expenses for all due active rules. Returns count created."""
        due_rules = await self.repo.list_due(today)
        created = 0
        for rule in due_rules:
            await self.expenses.create(
                user_id=rule.user_id,
                category_id=rule.category_id,
                payment_method_id=rule.payment_method_id,
                recurring_rule_id=rule.id,
                amount=rule.amount,
                currency=rule.currency,
                expense_date=rule.next_run_date,
                description=rule.description,
            )
            rule.next_run_date = rule.next_run_date + _FREQUENCY_DELTA[rule.frequency]
            created += 1
        await self.session.commit()
        return created
