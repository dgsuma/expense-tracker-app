# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 9: Kubernetes — Kustomize base (namespace, ConfigMap, Postgres StatefulSet with PVC, API/web Deployments with probes and resource limits, TLS Ingress), dev/prod overlays, secrets strategy (no committed secrets), FluxCD-ready layout, Kubernetes deployment doc.
- Phase 8: Docker hardening — multi-stage API and web Dockerfiles, non-root runtimes, health checks on all services, `.dockerignore`, nginx config with security headers and SPA fallback, full compose stack (db + api + web), build-arg base image for digest pinning, Docker deployment doc.
- Phase 7: testing — backend unit test suite (51 tests: security/hashing/JWT, schema validation, analytics period bounds, AuthService with mocked repos), pytest-cov with coverage config and gate, testing strategy doc. Unit coverage ~69% (DB-dependent layers covered by integration tests in CI).
- Phase 6: Flutter app — cross-platform (Android/iOS/tablet/web) with Riverpod state management, go_router auth-gated routing, Dio API client with automatic token refresh, secure token storage, login/register screens, dashboard (summary cards, category pie chart, spending trend bar chart, responsive wide/narrow layout), expense list with swipe-to-delete and add/edit form. Model unit tests; web release build verified.
- Phase 5: budgets + analytics — budget CRUD, budget-vs-actual with period bounds and subcategory rollup, analytics summaries (daily/weekly/monthly/annual), category breakdown with percentages, spending trends (day/week/month buckets), and CSV export (UTF-8 BOM, Excel-compatible).
- Phase 4: core expense APIs — categories (tree, subcategories, system defaults protected), payment methods, expenses (CRUD, soft delete/restore, search, filtering, pagination, whitelisted sorting), recurring rules (with run-due generation). Repository-level user_id isolation; reference validation; archive-instead-of-delete for referenced categories/payment methods.
- Phase 3: authentication — Argon2id password hashing, JWT access tokens (15 min), rotating opaque refresh tokens (SHA-256 hashed, 30-day) with reuse/theft detection that revokes the token family; endpoints for register/login/refresh/logout and `users/me` (get/patch/change-password); `get_current_user` dependency enforcing active-user auth; auth integration tests; DB engine `connect_timeout` for fail-fast.
- Phase 2: database layer — SQLAlchemy 2.0 models for all 7 tables (users, categories, payment_methods, expenses, recurring_rules, budgets, refresh_tokens) with UUID PKs, audit timestamps, soft delete, and naming conventions; Alembic wired to `database/alembic` with env-var-driven config; initial migration (with CITEXT extension); idempotent seed script for system default categories; `scripts/migrate.ps1` helper; model registration tests.
- Phase 1: FastAPI backend foundation — app factory, environment-based configuration (pydantic-settings), structured JSON logging (structlog) with request-ID middleware, centralized RFC 7807 exception handling, `/health` and `/ready` probes, async SQLAlchemy engine with lazy initialization, CORS from env, multi-stage Dockerfile (non-root), compose service, PowerShell dev scripts, and the first pytest suite.
- Phase 0: architecture and technology selection, repository skeleton, design documentation (architecture, database schema, API design, security model), roadmap, Docker Compose development configuration, Git initialization.
