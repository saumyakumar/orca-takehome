"""Shared base every foundation entity builds on.

Any app's entity that wants RBAC scoping, audit-ability, and soft-delete
for free just inherits OrcaBaseMixin alongside the declarative Base -
no per-app copy of these fields.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import declared_attr


def new_id() -> str:
    return str(uuid.uuid4())


class OrcaBaseMixin:
    id = Column(String, primary_key=True, default=new_id)
    country = Column(String, nullable=False, index=True)
    owner_app = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
