from typing import Optional

from sqlalchemy.orm import Session

from app.localization.models import Label


def get_label(db: Session, entity_type: str, field: str, key: str, locale: str, default: Optional[str] = None) -> str:
    row = (
        db.query(Label)
        .filter_by(entity_type=entity_type, field=field, key=key, locale=locale)
        .first()
    )
    return row.value if row else (default or key)
