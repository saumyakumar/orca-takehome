"""Lightest possible localization hook: a labels-by-locale lookup applied
to one field (Case.status), demonstrating the pattern without building
full i18n (locale negotiation, translated validation errors, etc.) - the
brief explicitly asks this stay minimal.
"""
from sqlalchemy import Column, String

from app.core.base_model import new_id
from app.db import Base


class Label(Base):
    __tablename__ = "labels"

    id = Column(String, primary_key=True, default=new_id)
    entity_type = Column(String, nullable=False)
    field = Column(String, nullable=False)
    key = Column(String, nullable=False)
    locale = Column(String, nullable=False)
    value = Column(String, nullable=False)
