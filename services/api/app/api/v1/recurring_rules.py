"""Recurring rule endpoints."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.recurring_rule import (
    RecurringRuleCreateRequest,
    RecurringRuleResponse,
    RecurringRuleUpdateRequest,
)
from app.services.recurring_rule import RecurringRuleService

router = APIRouter(prefix="/recurring-rules", tags=["recurring-rules"])


@router.get("", response_model=list[RecurringRuleResponse])
async def list_recurring_rules(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[RecurringRuleResponse]:
    rules = await RecurringRuleService(session).list(current_user.id)
    return [RecurringRuleResponse.model_validate(r) for r in rules]


@router.post("", response_model=RecurringRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_rule(
    body: RecurringRuleCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecurringRuleResponse:
    rule = await RecurringRuleService(session).create(user_id=current_user.id, **body.model_dump())
    return RecurringRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=RecurringRuleResponse)
async def update_recurring_rule(
    rule_id: UUID,
    body: RecurringRuleUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RecurringRuleResponse:
    rule = await RecurringRuleService(session).update(
        rule_id=rule_id, user_id=current_user.id, **body.model_dump(exclude_unset=True)
    )
    return RecurringRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await RecurringRuleService(session).delete(rule_id=rule_id, user_id=current_user.id)


@router.post("/run-due", status_code=status.HTTP_200_OK)
async def run_due_recurring_rules(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Generate expenses for all due active rules (also run by a scheduler later)."""
    created = await RecurringRuleService(session).run_due(today=datetime.now(UTC).date())
    return {"created": created}
