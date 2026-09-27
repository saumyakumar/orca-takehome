# Knowledge Graph — "I want to change X" → here's the file

Fast lookup for making a change without re-exploring the codebase. Organized by task, not by file.
For the big picture behind any of this, see [HLD.md](HLD.md).

## Backend

| I want to... | Go to | Notes |
|---|---|---|
| Change what a role can **see** (row visibility) | `backend/app/core/rbac.py` — `scoped_query()`, `ROLES_SEEING_ALL_COUNTRIES` | Applies identically to any model with a `country` column — Case, CountryStats, AuditLog all reuse it. |
| Change what a role can **do** (verb permission) | `backend/app/core/rbac.py` — `require_role()` | Called per-endpoint via `Depends(require_role(...))` — e.g. `cases/router.py`'s `create_case`/`update_case`/`close_case`. |
| Add a new **field** to Case | `backend/app/cases/models.py` (column) → `backend/app/cases/schemas.py` (`CaseCreate`/`CaseUpdate`/`CaseRead`) → `frontend/src/pages/CaseList.tsx` (table/state) + `frontend/src/components/CaseFormModal.tsx` (form) | Same order every time: model → schema → both frontend pieces that render/edit a case. |
| Change what triggers a **notification** | `backend/app/cases/router.py` — `_notify_on_assignment()` (create), `update_case`'s reassignment block | The actual send/store logic is `backend/app/core/notifications.py` — `NotificationService.notify()`. |
| Change **audit log** behavior (what's recorded, retention) | `backend/app/core/audit.py` — `AuditService`, `@audited()` decorator | List-style endpoints (no single entity) call `AuditService(db).record_action()` directly instead of using the decorator — see `list_cases`. |
| Add a **filter or search param** to the case list | `backend/app/cases/router.py` — `list_cases()` query params, applied on top of `scoped_query()` | Frontend: `frontend/src/pages/CaseList.tsx` — toolbar `<select>`/`<input>`s + the `load()` `URLSearchParams`. |
| Change **pagination** behavior | `backend/app/cases/router.py` — `limit`/`offset`/`CaseListResponse` | Frontend: `CaseList.tsx` — `PAGE_SIZE`, `offset` state, Previous/Next buttons. |
| Add a **new app** to the platform | New package mirroring `backend/app/cases/` (models.py, schemas.py, router.py) → register the router in `backend/app/main.py` → new page in `frontend/src/pages/` → one more entry in `App.tsx`'s `Sidebar` `items` array | `cases/` and `command_view/` never import each other — only talk via `core/events.py`. Keep it that way. |
| Change the **cross-app event flow** (e.g. what happens when a Case closes) | Publish side: `backend/app/cases/router.py::close_case` (`EVENT_BUS.publish(...)`). Subscribe side: `backend/app/command_view/service.py`. Wiring: `backend/app/main.py`'s `lifespan()` (`EVENT_BUS.subscribe(...)`). | New event types go in `backend/app/core/events.py`. |
| Change **login / current-user** info | `backend/app/main.py` — `GET /me` | This is the only thing the frontend should trust for role/country — see `UserContext.tsx` below. |
| Change **who can be assigned** a case, or the cross-country validation | `backend/app/cases/router.py` — `_validate_assignee_country()` | Mirrors on the frontend in `frontend/src/context/UserContext.tsx` — `assignableUsersForCountry()`. |
| Change the **localization** hook (labels by locale) | `backend/app/localization/service.py` — `get_label()`, `backend/app/localization/models.py` — `Label` | Currently applied to exactly one field: `Case.status` via `_with_label()` in `cases/router.py`. |
| Change **seeded demo data** | `backend/seed.py` | Note: run it with the same cwd the server uses (`orca.db` is a relative path — see "Known gotcha" below). |
| Add/change a **fake demo user** | `backend/app/auth/fake_users.py` — `FAKE_USERS` | Mirror any new user in `frontend/src/context/UserContext.tsx` — `DEMO_USERS` (and `ASSIGNABLE_USERS`/`country` if they should be assignable). |
| Change **CORS / app wiring / router registration** | `backend/app/main.py` | All routers get `app.include_router(...)`'d here; all model modules get imported here for `Base.metadata.create_all()`. |

## Frontend

| I want to... | Go to | Notes |
|---|---|---|
| Change the **nav / add a tab** | `frontend/src/App.tsx` — `Sidebar`'s `items` array + the `{tab === "x" && <X/>}` block in `Shell` | One tab = one app, by design — keep it that way even if a page temporarily needs to render inside another one. |
| Change **role-based UI visibility** (e.g. which filters a role sees) | Read `currentUser` from `frontend/src/context/UserContext.tsx` (sourced from `GET /me`) | Do **not** re-derive role/admin-ness from `DEMO_USERS` — that list is only for populating the "Viewing as" picker, not for permission decisions. |
| Change the **create/edit case form** | `frontend/src/components/CaseFormModal.tsx` | Takes a `country` prop that scopes the assignee dropdown — always pass the case's own country (or the new-case target country from `CaseList.tsx`'s `newCaseCountry`). |
| Change the **history view** | `frontend/src/components/CaseHistoryDrawer.tsx` | Calls `GET /cases/{id}/history` — any role that can see the case can see its history (different rule from the platform-wide Audit Log page). |
| Change **notification polling / display** | `frontend/src/components/NotificationBell.tsx` | 5s poll interval is `POLL_MS` at the top of the file. |
| Change the **API base path / error handling / auth header** | `frontend/src/api/client.ts` — `apiFetch()` | The one function every page/component uses to call the backend. |
| Change **design tokens** (colors, buttons, badges, nav styling) | `frontend/src/index.css` (`@layer components`) + `frontend/tailwind.config.js` (brand color ramp) | |
| Change the **"Viewing as" list** | `frontend/src/context/UserContext.tsx` — `DEMO_USERS` | Must match `backend/app/auth/fake_users.py`'s `FAKE_USERS` exactly (ids and countries). |

## Tests

| I want to test... | Go to |
|---|---|
| RBAC / row-visibility | `backend/tests/test_rbac_query_filtering.py` |
| Audit trail | `backend/tests/test_audit_trail.py` |
| Cross-app event flow | `backend/tests/test_event_flow.py` |
| Notifications | `backend/tests/test_notifications.py` |
| Pagination/search | `backend/tests/test_pagination_and_search.py` |
| Filters (country/assignee/status) | `backend/tests/test_case_filters.py` |
| Per-case history | `backend/tests/test_case_history.py` |
| Cross-country assignee validation | `backend/tests/test_assignee_country_validation.py` |

Shared fixtures (`client`, `db_session`, `auth_headers`, and the autouse `fresh_db` that resets the
DB per test) live in `backend/tests/conftest.py` — importing every model module here (and in
`main.py`) before `create_all()` is why a new entity must be imported in both places, or its table
never gets created.

## Known gotcha (not a code bug, an environment one)

`ORCA_DATABASE_URL` defaults to the relative path `sqlite:///./orca.db` (`backend/app/config.py`).
The seeded data only shows up if `seed.py` is run from the **same working directory** the server
is started from — running the server from the repo root but seeding from `backend/` (or vice versa)
silently creates two different empty/half-populated database files. If cases mysteriously vanish
after a restart, check this first before assuming a code regression.

## Layout map (fallback — "where even is X")

```
backend/app/
  main.py              FastAPI app, router registration, model imports, /me
  config.py            DATABASE_URL
  db.py                SQLAlchemy engine/session/Base
  core/                shared foundation (see HLD.md)
  cases/                Care Companion (Case)
  command_view/         Command View (CountryStats)
  audit_logs/            platform-wide GET /audit-logs
  notifications/          GET/POST /notifications
  localization/            Label / get_label
  auth/                     fake_users.py
backend/seed.py         demo data
backend/tests/           see table above

frontend/src/
  main.tsx             entry point
  App.tsx              shell, sidebar, tabs
  api/client.ts         apiFetch()
  context/UserContext.tsx  userId + currentUser (from /me) + DEMO_USERS/ASSIGNABLE_USERS
  pages/                CaseList, CommandView, AuditLog
  components/            CaseFormModal, CaseHistoryDrawer, NotificationBell
  index.css              design tokens
```
