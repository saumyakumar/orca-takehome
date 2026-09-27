from sqlalchemy import Column, Integer

from app.core.base_model import OrcaBaseMixin
from app.db import Base


class CountryStats(OrcaBaseMixin, Base):
    """One row per country. Deliberately still built on OrcaBaseMixin even
    though fields like created_by/owner_app are less load-bearing for an
    aggregate than for a transactional entity like Case - proving the
    same base serves both a "write-heavy" and a "read-heavy, derived"
    entity is the point of this pairing, not a coincidence."""

    open_case_count = Column(Integer, nullable=False, default=0)
