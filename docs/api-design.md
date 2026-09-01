# API design

Base path: `/api/v1`. OpenAPI/Swagger auto-generated at `/docs`, ReDoc at `/redoc`. All requests/responses JSON unless noted. All timestamps ISO 8601 UTC. Money as decimal strings in JSON (no float rounding).

## Conventions

- **Auth:** `Authorization: Bearer <access_token>` on all endpoints except `auth/register`, `auth/login`, `auth/refresh`, and ops endpoints.
- **Errors:** RFC 7807 problem+json — `{ "type", "title", "status", "detail", "instance", "request_id" }`. No stack traces in responses.
- **Pagination:** `?page=1&page_size=50` (max 100) → `{ "items": [...], "total", "page", "page_size" }`.
- **Filtering/sorting:** query params, e.g. `?from=2026-01-01&to=2026-01-31&category_id=...&search=...&sort=-expense_date`.
- **Idempotency:** create endpoints accept optional `Idempotency-Key` header (enforced from Phase 11).
- **Rate limiting:** 429 + `Retry-After` (Redis-backed from Phase 11; middleware hook present from Phase 1).

## Endpoint map

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account (email, password, display_name, default_currency) |
| POST | `/api/v1/auth/login` | Returns `{ access_token, refresh_token, expires_in }` |
| POST | `/api/v1/auth/refresh` | Rotate refresh token → new pair |
| POST | `/api/v1/auth/logout` | Revoke presented refresh token |

### Users
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/users/me` | Current profile |
| PATCH | `/api/v1/users/me` | Update display_name, default_currency |
| POST | `/api/v1/users/me/change-password` | Revokes all refresh tokens |

### Categories
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/categories` | Tree (parents with nested subcategories) |
| POST | `/api/v1/categories` | Create (optional `parent_id`) |
| GET/PATCH/DELETE | `/api/v1/categories/{id}` | Delete = archive if referenced |

### Payment methods
| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/v1/payment-methods` | List / create |
| PATCH/DELETE | `/api/v1/payment-methods/{id}` | Update / archive |

### Expenses
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/expenses` | Paginated list with filters (date range, category, payment method, amount range, free-text search) |
| POST | `/api/v1/expenses` | Create |
| GET/PATCH/DELETE | `/api/v1/expenses/{id}` | DELETE is soft delete |
| POST | `/api/v1/expenses/{id}/restore` | Undo soft delete |
| GET | `/api/v1/expenses/export?format=csv` | CSV export of filtered set (Excel-compatible; native xlsx later) |

### Recurring rules
| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/v1/recurring-rules` | List / create |
| GET/PATCH/DELETE | `/api/v1/recurring-rules/{id}` | Manage |
| POST | `/api/v1/recurring-rules/run-due` | Generate due expenses (also run by scheduler) |

### Budgets
| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/v1/budgets` | List / create |
| GET/PATCH/DELETE | `/api/v1/budgets/{id}` | Manage |
| GET | `/api/v1/budgets/vs-actual?period=monthly` | Budget vs actual per category + overall |

### Analytics
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/analytics/summary?period=daily\|weekly\|monthly\|annual&date=...` | Totals, count, average |
| GET | `/api/v1/analytics/by-category?from=&to=` | Totals + percentages per category |
| GET | `/api/v1/analytics/trends?from=&to=&granularity=day\|week\|month` | Time series for charts |

### Operations
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness (no dependencies) |
| GET | `/ready` | Readiness — checks DB connectivity |

## Versioning policy

Breaking changes → `/api/v2` mounted alongside v1; v1 maintained for a deprecation window. Non-breaking additions (new fields/endpoints) ship in v1.
