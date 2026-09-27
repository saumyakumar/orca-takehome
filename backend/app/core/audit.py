"""Generic, reusable audit trail.

One AuditLog table + one AuditService.record() call site, usable by any
entity with an .id and a .country - not a hand-rolled log call
duplicated per app. `audited()` is a route decorator that derives
entity_type/entity_id/actor from the handler's own return value and
injected `user`/`db`, so call sites don't repeat those as string
literals that could drift out of sync with the model.
"""
import json
from datetime import datetime
from functools import wraps
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import Session

from app.auth.fake_users import User
from app.core.base_model import new_id
from app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=new_id)
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    country = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    details = Column(String, nullable=True)


class AuditLogRead(BaseModel):
    """Shared read schema - used by the platform-wide /audit-logs endpoint
    and by any per-entity history endpoint (e.g. GET /cases/{id}/history)
    so both expose audit rows identically instead of duplicating shape."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    country: Optional[str]
    timestamp: datetime


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(self, actor: User, action: str, entity, details: Optional[dict] = None) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor.id,
                action=action,
                entity_type=type(entity).__name__,
                entity_id=entity.id,
                country=getattr(entity, "country", None),
                details=json.dumps(details) if details else None,
            )
        )
        self.db.commit()

    def record_action(self, actor: User, action: str) -> None:
        """For actions with no single entity (e.g. a list view)."""
        self.db.add(
            AuditLog(
                actor_id=actor.id,
                action=action,
                entity_type="—",
                entity_id="—",
                country=getattr(actor, "country", None),
            )
        )
        self.db.commit()


def audited(action: str):
    """Route decorator: after the handler returns an OrcaBaseMixin entity,
    record one audit row automatically. Falls back gracefully if the
    handler returns a list or None (no-op) rather than raising."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            user = kwargs.get("user")
            db = kwargs.get("db")
            if user is not None and db is not None and result is not None and hasattr(result, "id"):
                AuditService(db).record(actor=user, action=action, entity=result)
            return result

        return wrapper

    return decorator
