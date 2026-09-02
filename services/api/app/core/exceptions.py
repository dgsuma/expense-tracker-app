"""Centralized exception types and RFC 7807 problem+json responses.

All API errors share one shape:
    { "type", "title", "status", "detail", "instance", "request_id" }

Handlers are registered on the app in main.py. Unhandled exceptions are
logged with the request ID and returned as a generic 500 — internals and
stack traces never leak to clients.
"""

from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, client-facing application errors."""

    status_code: int = 500
    title: str = "Internal Server Error"
    error_type: str = "about:blank"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.title
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    title = "Not Found"


class UnauthorizedError(AppError):
    status_code = 401
    title = "Unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    title = "Forbidden"


class ConflictError(AppError):
    status_code = 409
    title = "Conflict"


class ServiceUnavailableError(AppError):
    status_code = 503
    title = "Service Unavailable"


def problem_body(
    *,
    status: int,
    title: str,
    detail: str,
    instance: str,
    request_id: UUID | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
        "request_id": str(request_id) if request_id else None,
    }
    if extra:
        body.update(extra)
    return body


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "request_error",
        status=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_body(
            status=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            instance=request.url.path,
            request_id=request_id,
        ),
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Convert framework-raised HTTPExceptions (404 unknown route, 405, etc.)
    into the same RFC 7807 shape as application errors. Registered against the
    Starlette base class so it also covers FastAPI's HTTPException subclass."""
    request_id = getattr(request.state, "request_id", None)
    title = exc.detail if isinstance(exc.detail, str) else "HTTP Error"
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_body(
            status=exc.status_code,
            title=title,
            detail=title,
            instance=request.url.path,
            request_id=request_id,
        ),
        headers=getattr(exc, "headers", None),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=422,
        content=problem_body(
            status=422,
            title="Validation Error",
            detail="Request validation failed.",
            instance=request.url.path,
            request_id=request_id,
            extra={"errors": exc.errors()},
        ),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=problem_body(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            instance=request.url.path,
            request_id=request_id,
        ),
    )
