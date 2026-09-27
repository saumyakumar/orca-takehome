from sqlalchemy import Column, String

from app.core.base_model import OrcaBaseMixin
from app.db import Base


class Case(OrcaBaseMixin, Base):
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")  # "open" | "closed"
    assigned_to = Column(String, nullable=True)
