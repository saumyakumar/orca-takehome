from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.fake_users import FAKE_USERS, User
from app.cases.models import Case
from app.cases.schemas import CaseCreate, CaseListResponse, CaseRead, CaseUpdate
from app.core.audit import AuditLog, AuditLogRead, AuditService, audited
from app.core.deps import get_current_user
from app.core.events import EVENT_BUS, CaseClosed
from app.core.notifications import NotificationService
from app.core.rbac import Role, get_scoped_or_404, require_role, scoped_query
from app.db import get_db
from app.localization.service import get_label

router = APIRouter(prefix="/cases", tags=["cases"])


def _validate_assignee_country(assigned_to: Optional[str], case_country: str) -> None:
    """A case can only be assigned to staff in its own country - assigning
    across countries is nonsensical (that person has no scoped_query()
    visibility into the case at all) and, unchecked, would be exactly the
    kind of data-layer gap this codebase otherwise avoids: the UI can
    choose not to *offer* a bad option, but only a server-side check
    actually prevents one."""
    if not assigned_to:
        return
    assignee = FAKE_USERS.get(assigned_to)
    if assignee is None or assignee.country != case_country:
        raise HTTPException(
            status_code=400,
            detail=f"Assignee must be staff in {case_country}",
        )


def _notify_on_assignment(db: Session, case: Case, assigned_to: Optional[str]) -> None:
    """Notify the new assignee, or - if the case is left unassigned - the
    country's Country Lead(s), so an unassigned case doesn't just sit
    silently. Reuses FAKE_USERS as the demo "who's who" directory; a real
    auth system would query a users table by role+country instead."""
    notifications = NotificationService(db)
    if assigned_to:
        notifications.notify(
            recipient_id=assigned_to,
            message=f"You were assigned case '{case.title}'",
            entity=case,
        )
        return
    leads = [
        u for u in FAKE_USERS.values() if u.role == Role.COUNTRY_LEAD and u.country == case.country
    ]
    for lead in leads:
        notifications.notify(
            recipient_id=lead.id,
            message=f"New unassigned case needs attention: '{case.title}'",
            entity=case,
        )


def _with_label(case: Case, db: Session, locale: str) -> CaseRead:
    read = CaseRead.model_validate(case)
    read.status_label = get_label(db, "Case", "status", case.status, locale, default=case.status)
    return read


@router.get("", response_model=CaseListResponse)
def list_cases(
    locale: str = "en",
    search: Optional[str] = None,
    country: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # RBAC enforced here: scoped_query() adds the country filter as a SQL
    # WHERE clause before .all() runs - it never fetches every row and
    # filters in Python (that anti-pattern is exactly what Part D flags).
    # search/filters/pagination are all applied on top of that already-
    # scoped query, never before it - a non-admin passing a `country`
    # outside their own scope just gets zero rows (scoped_query already
    # restricted the base query), never a bypass.
    query = scoped_query(db, Case, user)
    if search:
        query = query.filter(Case.title.ilike(f"%{search}%"))
    if country:
        query = query.filter(Case.country == country)
    if assigned_to:
        if assigned_to == "unassigned":
            query = query.filter(Case.assigned_to.is_(None))
        else:
            query = query.filter(Case.assigned_to == assigned_to)
    if status:
        query = query.filter(Case.status == status)
    total = query.count()
    cases = query.order_by(Case.created_at.desc()).offset(offset).limit(limit).all()
    AuditService(db).record_action(actor=user, action="list_cases")
    return CaseListResponse(
        items=[_with_label(c, db, locale) for c in cases],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{case_id}/history", response_model=list[AuditLogRead])
def get_case_history(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Same visibility rule as viewing the case itself (get_scoped_or_404
    # already 404s for out-of-country ids) - deliberately NOT restricted
    # to Admin/Auditor like the platform-wide /audit-logs endpoint below.
    # "Who touched this record" is part of managing it; "everything
    # everyone did platform-wide" is a separate, compliance-level concern.
    case = get_scoped_or_404(db, Case, user, case_id)
    return (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "Case", AuditLog.entity_id == case.id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: str, locale: str = "en", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    case = get_scoped_or_404(db, Case, user, case_id)
    return _with_label(case, db, locale)


@router.post("", response_model=CaseRead)
@audited("create")
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.COUNTRY_LEAD, Role.FIELD_WORKER)),
):
    country = user.country if user.role != Role.ADMIN else "Arnova"
    _validate_assignee_country(payload.assigned_to, country)
    case = Case(
        title=payload.title,
        description=payload.description,
        assigned_to=payload.assigned_to,
        country=country,
        owner_app="care_companion",
        created_by=user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    _notify_on_assignment(db, case, case.assigned_to)
    return case


@router.patch("/{case_id}", response_model=CaseRead)
@audited("update")
def update_case(
    case_id: str,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.COUNTRY_LEAD)),
):
    case = get_scoped_or_404(db, Case, user, case_id)
    changes = payload.model_dump(exclude_unset=True)
    if "assigned_to" in changes:
        _validate_assignee_country(changes["assigned_to"], case.country)
    previous_assignee = case.assigned_to
    for field, value in changes.items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    if "assigned_to" in changes and case.assigned_to and case.assigned_to != previous_assignee:
        NotificationService(db).notify(
            recipient_id=case.assigned_to,
            message=f"You were assigned case '{case.title}'",
            entity=case,
        )
    return case


@router.post("/{case_id}/close", response_model=CaseRead)
@audited("close")
def close_case(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.COUNTRY_LEAD)),
):
    case = get_scoped_or_404(db, Case, user, case_id)
    case.status = "closed"
    db.commit()
    db.refresh(case)
    # cases/ never imports command_view/ - it only publishes an event.
    # Any app (Command View today, a 4th app tomorrow) can subscribe.
    EVENT_BUS.publish(CaseClosed(case_id=case.id, country=case.country))
    return case
