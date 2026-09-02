"""Payment method model (cash, card, bank, ...)."""

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, uuid_pk


class PaymentMethodType(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK = "bank"
    OTHER = "other"


class PaymentMethod(Base, TimestampMixin):
    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentMethodType.OTHER.value
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
