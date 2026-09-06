"""FastAPI application factory and module-level app instance.

Run locally:   uvicorn app.main:app --reload
Run in Docker: see infrastructure/docker/api.Dockerfile
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.ops import router as ops_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import RateLimitMiddleware, build_redis_client
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Expense Tracker API",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        # Hide interactive docs in production deployments.
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Middleware (outermost last added → request context wraps CORS responses)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # Rate limiting (Redis-backed when REDIS_URL is set; no-op otherwise).
    # The Redis client is built lazily on first request to avoid blocking startup.
    redis_client_holder: dict = {}

    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):  # type: ignore[no-untyped-def]
        if "client" not in redis_client_holder:
            redis_client_holder["client"] = await build_redis_client()
        if redis_client_holder["client"] is None:
            return await call_next(request)
        middleware = RateLimitMiddleware(app, redis_client_holder["client"])
        return await middleware.dispatch(request, call_next)

    # Centralized exception handling (RFC 7807 problem+json)
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)

    # Routers
    app.include_router(ops_router)
    app.include_router(api_v1_router)

    return app


app = create_app()
