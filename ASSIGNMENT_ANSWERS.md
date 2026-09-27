# Assignment Answers

## Part A — Design Notes

`README.md` covers what this project is and how to run it. This section covers *why* it was built
this way — the design reasoning a grader would look for.

### Why these two apps

- **Case + Command View implements one of the two required cross-app integration flows** (closing a
  Case updates Command View's aggregate count) rather than inventing a new one — reusing a
  pre-defined contract instead of designing and defending a novel one from scratch under a time budget.
- **Case and CountryStats are structurally opposite entities**: Case is mutable, stateful, and
  written to constantly; CountryStats is a near-read-only, derived aggregate, one row per country.
  Proving that one shared base model and one RBAC helper serve both is a harder, more convincing
  test of "does this foundation genuinely generalise" than pairing two structurally similar
  entities would be.
- **Deliberate link to the separate code-review exercise**: that exercise's reviewed code is a
  `Case`-entity service that fetches all cases and filters by country in Python afterward. Case is
  built here with RBAC enforced as a SQL predicate instead, specifically so this codebase is a
  working counter-example to that anti-pattern, not just an assertion that the difference is
  understood.

### The core design judgment call

`app/core/` is the entire shared foundation; `app/cases/` and `app/command_view/` only *consume*
it and never import each other directly. A third entity needs only: inherit `OrcaBaseMixin`, write
a router calling `scoped_query()` — zero changes to `core/`. `scoped_query()` is reused a third
time for `AuditLog`, which doesn't even inherit the full mixin — proof the helper only needs the
one field (`country`) it actually depends on, not the whole shape.

`scoped_query()` (see `core/rbac.py`) filters by country as a SQL `WHERE` clause, before any row is
fetched — deliberately not the anti-pattern of fetching everything and filtering in Python
afterward (which doesn't scale, and fails *open*: a forgotten filter step silently leaks every
country's data instead of erroring). `tests/test_rbac_query_filtering.py` proves enforcement
happens in SQL, not Python.

### RBAC: two independent checks, kept separate on purpose

Row visibility (`scoped_query()`) and verb permission (`require_role()`) answer different
questions — an Auditor is scoped to one country *and* barred from writing, while a Country Lead is
scoped to one country but *can* write. Merging them would force every future role combination into
special-cased logic instead of composing two orthogonal pieces.

### Time spent

_TODO: fill in your own honest total before submitting — it should reflect your actual time, not an
estimate I can make on your behalf._

## Part B — Infrastructure & Hosting Strategy

https://docs.google.com/document/d/16cJa2kuB9p4h_cXw916f0jEaW1pnGzpLzZWSw3whl0Q/edit?tab=t.0

## Part C — Delivery Leadership & Sequencing

https://docs.google.com/document/d/1uNXOybha78Iyna5qNVMsjBDKB9GxbPqRODHUgMmSpoU/edit?tab=t.0

## Part D — Code Review

https://docs.google.com/document/d/1QaaUlLcBXxiQ8_4jJ2hNKp5mVRXMdEEKKUXZZ4LSaMc/edit?tab=t.0
