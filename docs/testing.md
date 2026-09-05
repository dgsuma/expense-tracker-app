# Testing strategy

## Backend (pytest)

Two tiers, distinguished by whether they need a live database:

### Unit tests (no database)
Run anywhere, fast. Cover pure logic and use mocked repositories for services.

| File | Covers |
|---|---|
| `tests/test_ops.py` | Health/readiness endpoints, RFC 7807 errors, request-ID middleware |
| `tests/test_models.py` | Model registration, schema conventions |
| `tests/test_security.py` | Argon2 hashing, JWT create/decode/expiry/tamper, refresh token hashing |
| `tests/test_schemas.py` | Pydantic validation (password strength, amount > 0, email) |
| `tests/test_analytics_service.py` | Period-bound logic (daily/weekly/monthly/annual, leap years) |
| `tests/test_auth_service.py` | AuthService with mocked repos (register/login/refresh/logout/change-password, theft detection) |

```powershell
cd services\api
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\test_auth.py
```

### Integration tests (need a database)
Exercise the real request → service → repository → database path. These run in
CI (where Postgres is available) and against the local compose stack.

| File | Covers |
|---|---|
| `tests/test_auth.py` | Full auth flows against a live API + DB |

```powershell
# Requires the compose stack running (docker compose up -d)
cd services\api
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py
```

> **Note on this dev machine:** host→DB asyncpg connections from pytest hang,
> so integration tests are verified against the running container via curl
> instead. They run normally in CI.

### Coverage

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\test_auth.py --cov=app --cov-report=term-missing
```

- Unit tests alone: **~69%** (DB-dependent repositories/services are exercised by integration tests).
- CI gate: **≥80%** on the combined unit + integration run (enforced in the Jenkins pipeline, Phase 10).

## Frontend (Flutter)

```powershell
cd apps\mobile
flutter analyze   # static analysis
flutter test      # unit/widget tests
```

- `test/models_test.dart` — model JSON parsing (User, Category tree, Expense, ExpensePage).
- Widget tests that boot the full app are avoided because `flutter_secure_storage`
  has no test implementation; logic is tested via unit tests and the app is
  validated with `flutter build web`.

## Conventions

- One test file per module under test, named `test_<module>.py`.
- Unit tests must not touch the database, network, or filesystem — mock at the repository boundary.
- Integration tests use unique data per run (UUID-suffixed emails) so they are idempotent.
