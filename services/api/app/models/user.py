"""User account model."""

import enum
import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    categories: Mapped[list["Category"]] = relationship(back_populates="user")  # noqa: F821
    expenses: Mapped[list["Expense"]] = relationship(back_populates="user")  # noqa: F821
