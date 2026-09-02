"""Operational endpoints: liveness and readiness probes.

/health — no dependencies; the process is up. Used by Docker/Kubernetes liveness.
/ready  — verifies database connectivity. Used by readiness probes and compose
          healthchecks so dependent services only start against a working stack.
"""

from fastapi import APIRouter, Response, status

from app.db.session import ping_database

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(response: Response) -> dict[str, str]:
    if await ping_database():
        return {"status": "ready", "database": "up"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "database": "down"}
