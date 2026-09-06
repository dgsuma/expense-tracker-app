"""Billing service boundary.

Defines the interface for subscription/billing operations. The current
implementation is a no-op "free tier" — every user has full access and no
usage limits are enforced. A real implementation (Stripe, Chargebee, etc.)
plugs in behind this interface without changing the rest of the application.

This is intentionally minimal: no payment processing is built yet, but the
boundary exists so commercial features can be added without redesign.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    max_expenses_per_month: int | None  # None = unlimited
    max_users: int


FREE_PLAN = Plan(code="free", name="Free", max_expenses_per_month=None, max_users=1)


class BillingService(ABC):
    """Interface for subscription and usage-limit operations."""

    @abstractmethod
    async def get_plan(self, user_id: UUID) -> Plan:
        """The plan a user is on."""

    @abstractmethod
    async def check_usage_limit(self, user_id: UUID, resource: str) -> bool:
        """True if the user may create another `resource` (e.g. 'expense')."""

    @abstractmethod
    async def is_feature_enabled(self, user_id: UUID, feature: str) -> bool:
        """True if a premium feature (e.g. 'ocr', 'multi_currency') is available."""


class FreeTierBillingService(BillingService):
    """No-op implementation: everyone is on the free plan, nothing is limited."""

    async def get_plan(self, user_id: UUID) -> Plan:
        return FREE_PLAN

    async def check_usage_limit(self, user_id: UUID, resource: str) -> bool:
        return True

    async def is_feature_enabled(self, user_id: UUID, feature: str) -> bool:
        return True


def get_billing_service() -> BillingService:
    """Factory — swap the implementation here when billing is introduced."""
    return FreeTierBillingService()
