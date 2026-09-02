"""Category model with self-referencing parent for one-level subcategories.

user_id NULL marks a system default category (seeded, shared, read-only for
users). kind='income' keeps the schema ready for future income tracking.
"""

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, TimestampMixin, uuid_pk


class CategoryKind(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "parent_id", "name", name="category_name_per_parent"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(10), nullable=False, default=CategoryKind.EXPENSE.value
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User | None"] = relationship(back_populates="categories")  # noqa: F821
    parent: Mapped["Category | None"] = relationship(remote_side=[id])
