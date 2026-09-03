"""Category endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdateRequest,
)
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryTreeNode])
async def list_categories(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[CategoryTreeNode]:
    return await CategoryService(session).list_tree(current_user.id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    category = await CategoryService(session).create(
        user_id=current_user.id, name=body.name, parent_id=body.parent_id, kind=body.kind
    )
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    category = await CategoryService(session).update(
        category_id=category_id,
        user_id=current_user.id,
        name=body.name,
        is_archived=body.is_archived,
    )
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await CategoryService(session).delete(category_id=category_id, user_id=current_user.id)
