# Expense Tracker

A production-ready, cross-platform expense tracking application built with a clean multi-tier architecture.

- **Mobile / tablet / web:** Flutter (Android, iOS, responsive web)
- **Backend:** Python 3.12 + FastAPI, SQLAlchemy 2.0 (async), Alembic
- **Database:** PostgreSQL 16
- **Deployment:** Docker / docker-compose locally, Kubernetes + Kustomize + FluxCD in the private cloud

## Repository layout

| Path | Contents |
|---|---|
| `apps/mobile` | Flutter app (Android / iOS / tablet) |
| `apps/web` | Flutter Web target |
| `services/api` | FastAPI backend service |
| `database` | Alembic migrations, seeds, schema docs |
| `infrastructure/docker` | Dockerfiles |
| `infrastructure/kubernetes` | Kustomize base + overlays (FluxCD-ready) |
| `scripts` | PowerShell development/ops scripts |
| `docs` | Architecture, API, security, and operations documentation |
| `tests` | Cross-cutting integration test suites |

## Quick start (local development)

Prerequisites: Docker Desktop, Python 3.12+, Flutter SDK, VS Code.

```powershell
# 1. Copy environment template and fill in local values
Copy-Item .env.example .env
#    (edit .env: set POSTGRES_PASSWORD and JWT_SECRET_KEY)

# 2. One-time API environment setup
.\scripts\setup-api.ps1

# 3. Start the database
docker compose up -d db

# 4. Run the API with hot reload  →  http://127.0.0.1:8000/docs
.\scripts\dev-api.ps1

# 5. Flutter app (from Phase 6 onward)
# .\scripts\dev-app.ps1
```

### Other common commands

```powershell
.\scripts\test-api.ps1          # run backend tests
.\scripts\lint-api.ps1          # lint + format check (-Fix to auto-fix)
docker compose up -d --build    # full containerized stack (db + api)
docker compose down             # stop everything
```

## Documentation

- [Architecture & technology decisions](docs/architecture.md)
- [Database schema](docs/database-schema.md)
- [API design](docs/api-design.md)
- [Security model](docs/security-model.md)
- [Roadmap](ROADMAP.md)
- [Security policy](SECURITY.md)

## Status

**Phase 1 — backend foundation complete.** See [ROADMAP.md](ROADMAP.md) for the phased implementation plan.
