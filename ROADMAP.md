# Roadmap

Each phase ends at a verifiable checkpoint. No phase starts before the previous checkpoint passes.

| Phase | Deliverable | Checkpoint | Status |
|---|---|---|---|
| 0 | Architecture, stack selection, repo skeleton, design docs, Git init | Docs reviewed & approved | ✅ Done |
| 1 | Backend foundation: FastAPI app factory, env config, structured logging, centralized exceptions, `/health` + `/ready`, Dockerfile | `GET /health` → 200 in container | ✅ Done |
| 2 | Database layer: SQLAlchemy models, Alembic setup, initial migration, compose Postgres, seed script | `alembic upgrade head` clean; tables present | ✅ Done |
| 3 | Authentication: register/login/refresh/logout, Argon2id, JWT, token rotation | Auth integration tests pass | ✅ Done |
| 4 | Core APIs: categories, payment methods, expenses CRUD, search/filter/pagination, recurring rules | Swagger-verified CRUD; isolation tests pass | ✅ Done |
| 5 | Budgets + analytics: summaries, by-category, trends, budget-vs-actual, CSV export | Report endpoints verified against fixtures | ✅ Done |
| 6 | Flutter app: auth flow, expense CRUD, categories, dashboards/charts, responsive phone/tablet/web | Runs on Android emulator + Chrome; golden tests | ✅ Done |
| 7 | Testing: unit + integration suites, coverage gate (≥80% backend) | `pytest` green locally and in container | ✅ Done |
| 8 | Docker hardening: multi-stage builds, non-root users, health checks, full compose stack | `docker compose up` → full stack healthy | ⬜ |
| 9 | Kubernetes: Kustomize base + dev/prod overlays, secrets strategy | `kustomize build` valid for both overlays | ⬜ |
| 10 | CI/CD: Jenkinsfile (lint → test → build → scan → push → GitOps update), GitOps repo layout | Pipeline stages documented & dry-run | ⬜ |
| 11 | Production hardening: Redis rate limiting, backup CronJob, security headers, billing interface boundary, audit review | Security checklist sign-off | ⬜ |

## Post-1.0 (commercial)

- Multi-tenancy (`households`/`tenants` layer)
- Subscription plans + billing integration (behind `BillingService` interface)
- Income tracking (schema-ready via `categories.kind`)
- Receipt upload + OCR (schema-ready via `expenses.metadata`)
- Accounts/balances
- Public SaaS deployment / AWS migration (EKS + RDS)
