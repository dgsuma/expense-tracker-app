# Docker deployment

All server-side components are containerized. The full stack runs locally with Docker Compose.

## Images

| Image | Dockerfile | Purpose |
|---|---|---|
| `expense-tracker-api` | [infrastructure/docker/api.Dockerfile](../infrastructure/docker/api.Dockerfile) | FastAPI backend |
| `expense-tracker-web` | [infrastructure/docker/web.Dockerfile](../infrastructure/docker/web.Dockerfile) | Flutter web bundle served by nginx |
| `postgres:16-alpine` | (official) | Database |

## Hardening applied

- **Multi-stage builds** — build tools are not in the runtime image.
- **Non-root runtime** — the API runs as the `app` user; nginx serves on unprivileged port 8080.
- **Health checks** — every service has a `HEALTHCHECK`; compose `depends_on` uses `service_healthy`.
- **`.dockerignore`** — secrets, `.env`, tests, docs, and build artifacts are excluded from the build context.
- **Build-arg base image** — the API base image is parameterized (`PYTHON_IMAGE`) so CI can pin a digest.
- **Security headers** — nginx sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- **Immutable static assets** — Flutter's content-hashed assets are cached for 1 year.

## Running the full stack

```powershell
# From the repo root (requires .env — copy from .env.example)
docker compose up -d --build

# Services:
#   web  → http://localhost:8080
#   api  → http://localhost:8000  (docs at /docs)
#   db   → localhost:5432

docker compose ps        # status
docker compose logs -f   # follow logs
docker compose down      # stop
```

## Configuration

All configuration is via environment variables (see [.env.example](../.env.example)):

- `POSTGRES_PASSWORD` (required), `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PORT`
- `JWT_SECRET_KEY` (required in production), token TTLs
- `API_PORT`, `API_CORS_ORIGINS`
- `WEB_PORT`, `WEB_API_BASE_URL` (the URL the browser uses to reach the API)

## Building individual images

```powershell
# API
docker build -f infrastructure/docker/api.Dockerfile -t expense-tracker-api .

# Web (inject the API URL the browser should use)
docker build -f infrastructure/docker/web.Dockerfile -t expense-tracker-web `
  --build-arg API_BASE_URL=http://localhost:8000 .
```

## Production notes

- Pin base image digests in CI (`--build-arg PYTHON_IMAGE=python:3.12-slim@sha256:...`).
- Scan images with Trivy in the pipeline (Phase 10).
- Never bake `.env` or secrets into images — inject at runtime via the orchestrator.
- The web image is static; scale it behind a CDN or ingress. The API is stateless and scales horizontally.
