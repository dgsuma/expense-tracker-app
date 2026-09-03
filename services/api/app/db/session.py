"""Async SQLAlchemy engine and session factory.

The engine is created lazily so importing the app never requires a reachable
database (important for tests and for /health, which must stay dependency-free).
ORM models and Alembic migrations arrive in Phase 2; the readiness probe
already verifies real connectivity here.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            # Fail fast rather than hang when the DB is unreachable (tests, misconfig).
            connect_args={"connect_timeout": 10},
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def ping_database() -> bool:
    """True if a trivial query succeeds. Used by the /ready probe."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — readiness must never raise
        return False


async def dispose_engine() -> None:
    """Close the pool (app shutdown / tests)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
