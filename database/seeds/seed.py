"""Seed script: system default categories (idempotent).

Run after migrations:
    python database/seeds/seed.py

System categories have user_id = NULL — shared, read-only for users.
Users can create their own categories on top (Phase 4).
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.category import Category, CategoryKind

DEFAULT_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Groceries", []),
    ("Dining", ["Restaurants", "Coffee & Snacks", "Takeaway"]),
    ("Housing", ["Rent / Mortgage", "Utilities", "Maintenance"]),
    ("Transport", ["Fuel", "Public Transport", "Parking", "Taxi / Rideshare"]),
    ("Health", ["Pharmacy", "Doctor", "Fitness"]),
    ("Entertainment", ["Streaming", "Hobbies", "Events"]),
    ("Shopping", ["Clothing", "Electronics", "Home"]),
    ("Travel", ["Flights", "Accommodation"]),
    ("Education", []),
    ("Insurance", []),
    ("Subscriptions", []),
    ("Other", []),
]


def database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "expense_app")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "expense_tracker")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def seed() -> None:
    engine = create_async_engine(database_url())
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(select(Category.name).where(Category.user_id.is_(None)))
        existing_names = {row[0] for row in result.all()}

        created = 0
        for parent_name, children in DEFAULT_CATEGORIES:
            if parent_name in existing_names:
                continue
            parent = Category(name=parent_name, kind=CategoryKind.EXPENSE.value, user_id=None)
            session.add(parent)
            await session.flush()  # assign parent.id
            for child_name in children:
                session.add(
                    Category(
                        name=child_name,
                        kind=CategoryKind.EXPENSE.value,
                        user_id=None,
                        parent_id=parent.id,
                    )
                )
            created += 1

        await session.commit()

    await engine.dispose()
    print(
        f"Seed complete: {created} parent categories created "
        f"({len(existing_names)} already present)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
