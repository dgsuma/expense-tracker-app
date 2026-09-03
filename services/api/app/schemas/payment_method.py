"""Payment method schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentMethodCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: str = Field(default="other", pattern="^(cash|card|bank|other)$")


class PaymentMethodUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: str | None = Field(default=None, pattern="^(cash|card|bank|other)$")
    is_archived: bool | None = None


class PaymentMethodResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    type: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
