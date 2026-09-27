"""Role-based access control enforced at the query layer.

scoped_query() is the one function every entity's "list"/"get" endpoint
calls. It adds the country filter as a SQL predicate on the Query object
*before* any rows are fetched - it never fetches everything and filters
in Python. Any model built on OrcaBaseMixin (it only needs a `country`
and `is_deleted` column) can be passed in unmodified.

Row-visibility (scoped_query) and verb-permission (require_role) are kept
as two separate, composable checks: which rows you can see and which
actions you're allowed to take are independent questions - e.g. an
Auditor is scoped to their own country AND barred from writing, while a
Country Lead is scoped to their own country but can write.
"""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Query, Session

from app.auth.fake_users import User
from app.core.deps import get_current_user
from app.core.roles import Role

ROLES_SEEING_ALL_COUNTRIES = {Role.ADMIN}


def scoped_query(db: Session, model, user: User) -> Query:
    """Query for `model`, already filtered by SQL WHERE clauses per the
    current user's role/country. Works for any model built on
    OrcaBaseMixin - Case, CountryStats, AuditLog, or any future entity."""
    query = db.query(model)
    if hasattr(model, "is_deleted"):
        query = query.filter(model.is_deleted.is_(False))
    if user.role in ROLES_SEEING_ALL_COUNTRIES:
        return query
    return query.filter(model.country == user.country)


def get_scoped_or_404(db: Session, model, user: User, record_id: str):
    obj = scoped_query(db, model, user).filter(model.id == record_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def require_role(*roles: Role):
    """Verb-level permission dependency, orthogonal to row scoping above."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not permitted for this role")
        return user

    return checker
