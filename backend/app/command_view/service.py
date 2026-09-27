"""Subscribes to CaseClosed. Recomputes (does not decrement) the
country's open-case count from a fresh COUNT query - self-healing
against a duplicate or out-of-order event, which a decrement is not:
replay this handler any number of times for the same event and the
count is still correct.
"""
from app.cases.models import Case
from app.command_view.models import CountryStats
from app.core.events import CaseClosed
from app.db import SessionLocal


def recompute_open_count(country: str, db) -> CountryStats:
    open_count = (
        db.query(Case)
        .filter(Case.country == country, Case.status == "open", Case.is_deleted.is_(False))
        .count()
    )
    stats = db.query(CountryStats).filter_by(country=country).first()
    if stats is None:
        stats = CountryStats(
            country=country,
            owner_app="command_view",
            created_by="system",
            open_case_count=open_count,
        )
        db.add(stats)
    else:
        stats.open_case_count = open_count
    db.commit()
    db.refresh(stats)
    return stats


def on_case_closed(event: CaseClosed) -> None:
    # Own session, not the request's - this handler may run after the
    # publishing request's session/transaction has already been used.
    db = SessionLocal()
    try:
        recompute_open_count(event.country, db)
    finally:
        db.close()
