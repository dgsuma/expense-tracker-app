# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 2: database layer — SQLAlchemy 2.0 models for all 7 tables (users, categories, payment_methods, expenses, recurring_rules, budgets, refresh_tokens) with UUID PKs, audit timestamps, soft delete, and naming conventions; Alembic wired to `database/alembic` with env-var-driven config; initial migration (with CITEXT extension); idempotent seed script for system default categories; `scripts/migrate.ps1` helper; model registration tests.
- Phase 1: FastAPI backend foundation — app factory, environment-based configuration (pydantic-settings), structured JSON logging (structlog) with request-ID middleware, centralized RFC 7807 exception handling, `/health` and `/ready` probes, async SQLAlchemy engine with lazy initialization, CORS from env, multi-stage Dockerfile (non-root), compose service, PowerShell dev scripts, and the first pytest suite.
- Phase 0: architecture and technology selection, repository skeleton, design documentation (architecture, database schema, API design, security model), roadmap, Docker Compose development configuration, Git initialization.
