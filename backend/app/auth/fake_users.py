"""Deliberately fake auth for this take-home: no passwords, sessions, or
JWTs. The frontend's role switcher sends one of these ids as an
X-User-Id header. A production system swaps this module for real
auth/session handling without touching RBAC or audit - both only ever
depend on a `User` with .id, .role, .country.
"""
from dataclasses import dataclass

from app.core.roles import Role


@dataclass(frozen=True)
class User:
    id: str
    name: str
    role: Role
    country: str


FAKE_USERS: dict[str, User] = {
    "admin-1": User(id="admin-1", name="Ada (Admin)", role=Role.ADMIN, country="*"),
    "lead-arn": User(id="lead-arn", name="Amara (Country Lead, Arnova)", role=Role.COUNTRY_LEAD, country="Arnova"),
    "lead-bel": User(id="lead-bel", name="Boris (Country Lead, Belmara)", role=Role.COUNTRY_LEAD, country="Belmara"),
    "field-cal": User(id="field-cal", name="Carla (Field Worker, Calduria)", role=Role.FIELD_WORKER, country="Calduria"),
    "audit-arn": User(id="audit-arn", name="Amit (Auditor, Arnova)", role=Role.AUDITOR, country="Arnova"),
}
