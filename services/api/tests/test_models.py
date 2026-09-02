"""Phase 2 acceptance tests: model registration and schema conventions."""

from app.models import Base
from app.models.base import NAMING_CONVENTION

EXPECTED_TABLES = {
    "users",
    "categories",
    "payment_methods",
    "expenses",
    "recurring_rules",
    "budgets",
    "refresh_tokens",
}


def test_all_tables_registered() -> None:
    assert EXPECTED_TABLES == set(Base.metadata.tables.keys())


def test_every_table_has_audit_or_created_timestamp() -> None:
    for name, table in Base.metadata.tables.items():
        assert "created_at" in table.c, f"{name} missing created_at"


def test_expenses_uses_numeric_money_and_soft_delete() -> None:
    expenses = Base.metadata.tables["expenses"]
    assert expenses.c.amount.type.__class__.__name__ == "Numeric"
    assert "deleted_at" in expenses.c
    assert "metadata" in expenses.c


def test_naming_convention_present() -> None:
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"
