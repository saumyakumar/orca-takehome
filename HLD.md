# High-Level Design — ORCA Platform Foundation

Read this before making a change. It explains what exists and why. For "which file do I touch,"
see [KNOWLEDGE_GRAPH.md](KNOWLEDGE_GRAPH.md) instead — this doc explains the shape of the system,
that one is the fast lookup.

## What this is

A minimal shared platform foundation for ORCA (an emergency-relief platform), demonstrated with
two apps — **Care Companion** (Case management) and **Command View** (aggregate dashboard) — plus
a third, platform-wide concern, **Audit Log**. The point of the exercise (see `README.md`) is that
the foundation (RBAC, audit, base model, events) is proven to generalize across two structurally
different apps, not hardcoded to one.

Stack: Python/FastAPI backend, SQLite, React/TypeScript frontend (Vite + Tailwind), no real auth
(a fake `X-User-Id` header stands in for login — see "Known simplifications" below).

## Backend architecture: shared foundation + peer app packages

```
backend/app/
  core/            ← the shared foundation. Every app package imports from here; core imports
                       nothing from any app package. This one-directional rule is what makes the
                       foundation reusable instead of tangled.
    base_model.py    OrcaBaseMixin — id, country, owner_app, created_by, timestamps, soft-delete.
                      Any entity that wants RBAC + audit-ability inherits this.
    rbac.py          scoped_query() (row visibility, SQL-level) + require_role() (verb permission).
                      The one function every "list"/"get" endpoint calls.
    audit.py         AuditLog model + AuditService + @audited() decorator. One shared audit trail.
    notifications.py Notification model + NotificationService. Same shape as audit.py, deliberately.
    events.py        EVENT_BUS — in-process pub/sub for cross-app integration.
    roles.py         Role enum (admin, country_lead, field_worker, auditor).
    deps.py          get_current_user() — reads X-User-Id, looks up the fake user.

  cases/           ← Care Companion. Owns Case (extends OrcaBaseMixin). Publishes CaseClosed.
  command_view/    ← Command View. Owns CountryStats. Subscribes to CaseClosed, recomputes.
  audit_logs/      ← Exposes the platform-wide GET /audit-logs (Admin/Auditor only).
  notifications/   ← Exposes GET /notifications, POST /notifications/{id}/read (owner-scoped).
  localization/    ← Label model + get_label() — the one field (Case.status) demonstrating i18n.
  auth/            ← fake_users.py — the "who's who" directory this whole demo stands in on.
```

`cases/` and `command_view/` never import each other directly — only via `core/events.py`. This is
what lets a third app join without cases/command_view knowing it exists.

### A note on RBAC's two independent checks

`scoped_query()` (row visibility — *which* rows) and `require_role()` (verb permission — *which
actions*) are deliberately separate, composable checks, not one merged rule. An Auditor is
scoped to one country *and* barred from writing; a Country Lead is scoped to one country but *can*
write. Every router combines these two independently per endpoint — see `cases/router.py` for the
clearest example (`list_cases` only scopes; `close_case` scopes *and* requires a role).

### A note on "central vs. regional" data (Part B territory)

The current codebase runs one shared SQLite file — there's no physical multi-database split. That
split (which country's data must sit on which server) is a **production deployment** question, not
something this demo codebase needs to implement. What this codebase *does* already provide, which
any future multi-database version would build on directly, is that every restricted entity already
carries `country` as a first-class field (`OrcaBaseMixin`) and every read already goes through one
funnel (`scoped_query()`) — the thing a real routing-by-country layer would key off of.

## Frontend architecture

```
frontend/src/
  App.tsx              Shell: Sidebar (nav) + header (NotificationBell + RoleSwitcher) + main content.
                        One tab per app — adding an app means one more Sidebar entry + one more
                        `{tab === "x" && <X />}` line, same pattern as the backend's peer packages.
  context/
    UserContext.tsx     Owns `userId` (the "Viewing as" selection) and fetches `currentUser` from
                        GET /me whenever it changes — the single source of truth for role/country
                        on the frontend. UI decisions (e.g. which filters to show) should read
                        `currentUser`, never re-derive role/country locally.
  pages/
    CaseList.tsx        Care Companion's page: search/filters, table, pagination, wires up the
                        modal + drawer below.
    CommandView.tsx     Command View's page: polls /country-stats every 3s.
    AuditLog.tsx        Platform-wide audit page (403s cleanly for non-Admin/Auditor roles).
  components/
    CaseFormModal.tsx   Shared create/edit form (assignee options scoped to the case's country).
    CaseHistoryDrawer.tsx  Right-side slide-over showing one case's audit trail.
    NotificationBell.tsx   Polls /notifications every 5s.
  api/client.ts         The one fetch wrapper (adds X-User-Id, handles errors) everything uses.
```

## Request lifecycle — one concrete trace (closing a case)

1. User clicks "Close" in `CaseList.tsx` → `apiFetch("/cases/{id}/close", userId, {method: "POST"})`.
2. Request hits `cases/router.py::close_case`, gated by `require_role(ADMIN, COUNTRY_LEAD)`.
3. `get_scoped_or_404()` re-fetches the case through `scoped_query()` — a Field Worker or someone
   from another country gets a 404, not just a 403, at this step.
4. `case.status = "closed"`, `db.commit()`.
5. The `@audited("close")` decorator writes one `AuditLog` row automatically.
6. `EVENT_BUS.publish(CaseClosed(...))` — `cases/` doesn't know or care who's listening.
7. `command_view/service.py`'s subscriber recomputes `CountryStats.open_case_count` for that
   country from a fresh `COUNT(*)` (not a decrement — replaying the same event twice stays correct).
8. `CommandView.tsx`'s 3-second poll picks up the new count with no manual refresh.

## Data model summary

| Entity | Inherits `OrcaBaseMixin`? | Country-scoped? | Notes |
|---|---|---|---|
| `Case` | Yes | Yes (residency-style) | `assigned_to` must match the case's own country — enforced server-side, see `_validate_assignee_country`. |
| `CountryStats` | Yes | Yes | One row per country; recomputed, never decremented. |
| `AuditLog` | No (append-only, system-owned) | Has a `country` column | Still works with `scoped_query()` — proof the helper only needs the one field, not the full mixin. |
| `Notification` | No | No — owner-scoped instead | Row visibility is `recipient_id == current_user.id`, a deliberately different rule from country-based RBAC. |
| `Label` | No | No | Global reference data (locale-keyed), the localization hook. |

## Known simplifications (and their production alternative)

| Simplification here | Production alternative |
|---|---|
| Fake header-based auth (`X-User-Id`) | Real auth/session handling or JWT; `User` in `auth/fake_users.py` is the only file that would change — RBAC and audit only ever depend on `.id`/`.role`/`.country` |
| Synchronous in-process `EventBus` | A durable queue/outbox (e.g. SQS, Redis Streams) so a crashed subscriber doesn't lose the event |
| SQLite | Postgres, for concurrent writes and proper migrations (no Alembic here — tables are created via `create_all()`) |
| Frontend polls Command View every 3s | A push mechanism (WebSocket/SSE) if near-real-time matters more than simplicity |
