"""Versioned API router. Feature routers are mounted here as phases land:

- Phase 3: auth, users
- Phase 4: categories, payment-methods, expenses, recurring-rules
- Phase 5: budgets, analytics
"""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    budgets,
    categories,
    expenses,
    payment_methods,
    recurring_rules,
    users,
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(categories.router)
api_v1_router.include_router(payment_methods.router)
api_v1_router.include_router(expenses.router)
api_v1_router.include_router(recurring_rules.router)
api_v1_router.include_router(budgets.router)
api_v1_router.include_router(analytics.router)
