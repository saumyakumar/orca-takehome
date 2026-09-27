"""Run once to populate demo data: `python seed.py` from backend/.
Creates cases across two countries so the RBAC scoping is visible when
switching the frontend's role dropdown, plus a couple of localized
status labels for the optional localization hook.
"""
from app.cases.models import Case
from app.command_view.service import recompute_open_count
from app.db import Base, SessionLocal, engine
from app.localization.models import Label

from app.core import audit as _audit_models  # noqa: F401
from app.command_view import models as _command_view_models  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Case).count() > 0:
            print("Already seeded, skipping.")
            return

        cases = [
            Case(title="Shelter request - Family A", country="Arnova", owner_app="care_companion", created_by="lead-arn", status="open"),
            Case(title="Medical supply case", country="Arnova", owner_app="care_companion", created_by="lead-arn", status="open"),
            Case(title="Relocation - minor dependents", country="Belmara", owner_app="care_companion", created_by="lead-bel", status="open"),
            Case(title="Follow-up - closed intake", country="Belmara", owner_app="care_companion", created_by="lead-bel", status="closed"),
            Case(title="Field survey case", country="Calduria", owner_app="care_companion", created_by="field-cal", status="open"),
        ]
        db.add_all(cases)
        db.commit()

        db.add_all([
            Label(entity_type="Case", field="status", key="open", locale="en", value="Open"),
            Label(entity_type="Case", field="status", key="closed", locale="en", value="Closed"),
            Label(entity_type="Case", field="status", key="open", locale="fr", value="Ouvert"),
            Label(entity_type="Case", field="status", key="closed", locale="fr", value="Fermé"),
        ])
        db.commit()

        for country in ("Arnova", "Belmara", "Calduria"):
            recompute_open_count(country, db)

        print(f"Seeded {len(cases)} cases and recomputed country stats.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
