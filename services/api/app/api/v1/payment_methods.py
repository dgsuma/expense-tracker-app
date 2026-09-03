"""Payment method endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.payment_method import (
    PaymentMethodCreateRequest,
    PaymentMethodResponse,
    PaymentMethodUpdateRequest,
)
from app.services.payment_method import PaymentMethodService

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[PaymentMethodResponse]:
    methods = await PaymentMethodService(session).list(current_user.id)
    return [PaymentMethodResponse.model_validate(m) for m in methods]


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    body: PaymentMethodCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentMethodResponse:
    pm = await PaymentMethodService(session).create(
        user_id=current_user.id, name=body.name, type=body.type
    )
    return PaymentMethodResponse.model_validate(pm)


@router.patch("/{pm_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    pm_id: UUID,
    body: PaymentMethodUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentMethodResponse:
    pm = await PaymentMethodService(session).update(
        pm_id=pm_id,
        user_id=current_user.id,
        name=body.name,
        type=body.type,
        is_archived=body.is_archived,
    )
    return PaymentMethodResponse.model_validate(pm)


@router.delete("/{pm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    pm_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await PaymentMethodService(session).delete(pm_id=pm_id, user_id=current_user.id)
