from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.fake_users import User
from app.core.audit import AuditLog, AuditLogRead
from app.core.deps import get_current_user
from app.core.rbac import Role, require_role, scoped_query
from app.db import get_db

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.AUDITOR)),
):
    # AuditLog doesn't inherit OrcaBaseMixin (it's an append-only, system-
    # owned record, not a domain entity) but still has a `country` column,
    # so the same scoped_query() helper applies to a third "entity" shape
    # with no new code - a bonus generalization point beyond Case/Stats.
    return scoped_query(db, AuditLog, user).order_by(AuditLog.timestamp.desc()).all()
