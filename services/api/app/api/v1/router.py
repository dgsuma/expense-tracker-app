"""Versioned API router. Feature routers are mounted here as phases land:

- Phase 3: auth, users
- Phase 4: categories, payment-methods, expenses, recurring-rules
- Phase 5: budgets, analytics
"""

from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")
