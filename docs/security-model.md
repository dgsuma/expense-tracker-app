# Security model

## Authentication

- **Passwords:** Argon2id hashing (via `passlib`/`argon2-cffi`), per-user salt, memory-hard parameters. Minimum 12 chars with complexity check at registration.
- **Tokens:** JWT access tokens (15 min TTL, HS256 initially — key from env; RS256 when an IdP or key-rotation service is introduced). Refresh tokens: 30-day, opaque random, **rotated on every use**, stored only as hashes in `refresh_tokens`. Reuse of a rotated token revokes the whole token family (theft detection).
- **Logout:** revokes the presented refresh token. Change-password revokes all user tokens.
- **Future OAuth/OIDC:** the login boundary is a `TokenService` interface; an external IdP (Keycloak/Auth0) can replace the local issuer without changing resource endpoints.

## Authorization & data isolation

- `user_id` scoping enforced in the **repository layer** — every query filters by the authenticated user; cross-user access is impossible even if a router forgets a check.
- `role` column (`user`/`admin`) enables RBAC later; admin endpoints will live under `/api/v1/admin` with a dedicated dependency guard.
- PostgreSQL row-level security is an available additional layer for the multi-tenant phase.

## API hardening

- Centralized exception handler → RFC 7807 errors, no internals leaked; unhandled exceptions logged with request ID and returned as generic 500.
- Pydantic v2 validation on every input; strict types, length caps, enum whitelists.
- CORS: explicit origin allowlist from env (no `*` with credentials).
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, strict `Content-Security-Policy` on docs routes.
- Rate limiting: middleware hook from Phase 1; Redis-backed limits per IP + per user from Phase 11 (login endpoints stricter).
- Soft deletes + audit timestamps on all owned tables.

## Secrets & configuration

- All config via environment variables (pydantic-settings); `.env` for local dev only and gitignored; `.env.example` documents keys with placeholders.
- No secrets in Git, images, or manifests. Kubernetes: Secrets from an external secrets store (e.g. External Secrets Operator) in the target cluster — never committed.
- Jenkins credentials store holds registry/cluster credentials; pipeline references IDs, not values.

## Transport & storage

- TLS terminated at ingress; internal cluster traffic over the cluster network (mTLS via service mesh is a future option).
- DB volumes encrypted at rest in the target environment; backups encrypted before off-site storage.

## Dependency & supply chain

- `pip-audit` (Python) and `flutter pub outdated` + `dependabot` in CI; container images scanned (Trivy) in the Jenkins pipeline.
- Pinned dependency versions; lockfiles committed.

## Reporting

See [SECURITY.md](../SECURITY.md) for the vulnerability disclosure process.
