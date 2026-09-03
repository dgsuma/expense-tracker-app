"""Category schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    parent_id: UUID | None = None
    kind: str = Field(default="expense", pattern="^(expense|income)$")


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    is_archived: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    parent_id: UUID | None
    name: str
    kind: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryTreeNode(BaseModel):
    """A category with its subcategories nested."""

    id: UUID
    name: str
    kind: str
    is_archived: bool
    children: list["CategoryTreeNode"] = []

    model_config = {"from_attributes": True}


CategoryTreeNode.model_rebuild()
