# Git workflow

## Branches

- `main` — protected; always releasable. Direct pushes disabled.
- `feature/<phase>-<short-description>` — all work happens here, e.g. `feature/p1-backend-foundation`.
- `fix/<short-description>` — bug fixes.
- `chore/<short-description>` — tooling, deps, docs-only chores.

## Commits — Conventional Commits

```
<type>(<scope>): <summary>

[optional body]
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `build`, `ci`.
Scopes: `api`, `db`, `auth`, `mobile`, `web`, `infra`, `k8s`, `ci`, `docs`.

Examples:
- `feat(api): add expense CRUD endpoints`
- `feat(db): initial schema migration`
- `ci: add Jenkins pipeline skeleton`

## Flow

1. Branch from `main`: `git checkout -b feature/p1-backend-foundation`
2. Commit early and often with conventional messages.
3. Open a PR to `main`; use the PR template checklist.
4. Squash-merge after review; delete the feature branch.
5. Tag releases: `v0.1.0`, `v0.2.0`, … (semver; 0.x until Phase 11 completes).

## Rules

- Never commit `.env`, secrets, keystores, or dump files (enforced by `.gitignore`).
- Keep PRs scoped to one phase deliverable where practical.
