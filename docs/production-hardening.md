# Production hardening

This document covers the production-readiness measures applied in Phase 11 and the remaining operational checklist.

## Applied in Phase 11

### Rate limiting
- **Redis-backed, per-IP fixed-window** limits via [app/core/rate_limit.py](../services/api/app/core/rate_limit.py).
- Stricter buckets on auth endpoints: login 10/min, register 5/min, refresh 20/min; general API 200/min.
- **Fail-open** when Redis is unavailable (traffic is not blocked); disabled entirely when `REDIS_URL` is unset (local dev).
- Returns `429` with `Retry-After` and the RFC 7807 error shape.
- Redis runs as a Deployment in the cluster ([redis.yaml](../infrastructure/kubernetes/base/redis.yaml)).

### Security headers
- [app/core/security_headers.py](../services/api/app/core/security_headers.py) applies to all API responses:
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`.
- The web tier (nginx) sets its own headers — see [nginx.conf](../infrastructure/docker/nginx.conf).

### Backups
- **CronJob** ([backup.yaml](../infrastructure/kubernetes/base/backup.yaml)) runs `pg_dump` daily at 02:00, gzips to a persistent volume, and prunes backups older than 14 days.
- For production, ship dumps to object storage (S3/MinIO) for off-site retention; the CronJob command is the single place to add that.

### Billing boundary
- [app/services/billing.py](../services/api/app/services/billing.py) defines a `BillingService` interface (`get_plan`, `check_usage_limit`, `is_feature_enabled`) with a no-op `FreeTierBillingService`.
- No payment processing is built, but the boundary exists so subscriptions/usage limits can be added without redesign.

## Security checklist (audit)

| Area | Status |
|---|---|
| Password hashing (Argon2id) | ✅ |
| JWT access + rotating refresh tokens, theft detection | ✅ |
| Per-user data isolation at repository layer | ✅ |
| RFC 7807 errors, no stack traces leaked | ✅ |
| Input validation (Pydantic v2) | ✅ |
| Rate limiting (auth + general) | ✅ |
| Security headers (API + web) | ✅ |
| Secrets via env / external store, none committed | ✅ |
| CORS allowlist | ✅ |
| Soft deletes + audit timestamps | ✅ |
| Health/readiness probes | ✅ |
| Non-root containers, multi-stage builds | ✅ |
| Dependency + image scanning in CI | ✅ |
| Backups (scheduled, retained) | ✅ |
| TLS at ingress (cert-manager) | ✅ (manifest) |

## Remaining operational tasks (before public launch)

1. **Secrets** — wire External Secrets Operator or Sealed Secrets in the cluster.
2. **Backup off-siting** — add object-storage upload to the backup CronJob.
3. **Monitoring** — Prometheus metrics endpoint + Grafana dashboards; alert on error rate and latency.
4. **Log aggregation** — ship structured logs to Loki/ELK.
5. **Multi-currency** — aggregate amounts in a base currency (currently raw per-user currency).
6. **Monthly recurring-rule precision** — replace the 30-day approximation with calendar-accurate scheduling.
7. **Pen test** — external review before handling real user data at scale.

## Scaling notes

- The API is stateless → scale replicas horizontally; rate limiting is shared via Redis.
- Postgres: add PgBouncer for connection pooling at scale; move to RDS/managed Postgres for HA.
- Redis: single replica suffices for rate limiting; use managed/HA Redis for caching at scale.
