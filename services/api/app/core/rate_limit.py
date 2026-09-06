"""Rate limiting middleware.

Uses Redis when REDIS_URL is configured (distributed, works across replicas);
falls back to a no-op when it is not (local dev). Limits are per client IP,
with a stricter bucket for the auth endpoints.

Design: a fixed-window counter per (bucket, identifier, window). Simple and
sufficient for the current scale; a sliding-window or token-bucket algorithm
can replace the internals without changing the middleware contract.
"""

import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

# (path prefix, max requests, window seconds)
_LIMITS: list[tuple[str, int, int]] = [
    ("/api/v1/auth/login", 10, 60),
    ("/api/v1/auth/register", 5, 60),
    ("/api/v1/auth/refresh", 20, 60),
    ("/api/v1/", 200, 60),  # general API bucket
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._redis = redis_client

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self._redis is None:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        for prefix, max_requests, window in _LIMITS:
            if request.url.path.startswith(prefix):
                allowed, retry_after = await self._check(
                    bucket=prefix, identifier=client, limit=max_requests, window=window
                )
                if not allowed:
                    logger.warning("rate_limit_exceeded", path=request.url.path, client=client)
                    return JSONResponse(
                        status_code=429,
                        content={
                            "type": "about:blank",
                            "title": "Too Many Requests",
                            "status": 429,
                            "detail": "Rate limit exceeded. Try again later.",
                            "instance": request.url.path,
                        },
                        headers={"Retry-After": str(retry_after)},
                    )
                break  # only the first matching bucket applies

        return await call_next(request)

    async def _check(
        self, *, bucket: str, identifier: str, limit: int, window: int
    ) -> tuple[bool, int]:
        """Fixed-window counter. Returns (allowed, retry_after_seconds)."""
        now = int(time.time())
        window_start = now - (now % window)
        key = f"ratelimit:{bucket}:{identifier}:{window_start}"
        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, window)
            if count > limit:
                retry_after = window_start + window - now
                return False, max(retry_after, 1)
            return True, 0
        except Exception:  # Redis down → fail open (don't block traffic)
            logger.error("rate_limit_redis_error")
            return True, 0


async def build_redis_client():  # type: ignore[no-untyped-def]
    """Create a Redis client if REDIS_URL is configured, else None."""
    settings = get_settings()
    redis_url = getattr(settings, "redis_url", None)
    if not redis_url:
        return None
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        logger.info("rate_limit_redis_connected")
        return client
    except Exception:
        logger.error("rate_limit_redis_unavailable")
        return None
