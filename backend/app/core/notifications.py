"""Generic, reusable in-app notifications - the "if this were a real
product" stand-in for email/push, built the same shape as the audit
trail (core/audit.py): one model, one service, usable by any entity
with an .id and a .country, not a one-off "case assigned" special case.

Recipient scoping is deliberately NOT scoped_query() (core/rbac.py) -
that helper answers "which country can this user see," but a
notification belongs to one specific *user*, not a country. Row
visibility here is `recipient_id == current_user.id`, an orthogonal
access rule to country-based RBAC.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import Session

from app.core.base_model import new_id
from app.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=new_id)
    recipient_id = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    message: str
    entity_type: str
    entity_id: str
    is_read: bool
    created_at: datetime


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def notify(self, recipient_id: str, message: str, entity) -> None:
        self.db.add(
            Notification(
                recipient_id=recipient_id,
                message=message,
                entity_type=type(entity).__name__,
                entity_id=entity.id,
            )
        )
        self.db.commit()
