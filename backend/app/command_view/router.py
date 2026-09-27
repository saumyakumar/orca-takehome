from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.fake_users import User
from app.command_view.models import CountryStats
from app.command_view.schemas import CountryStatsRead
from app.core.deps import get_current_user
from app.core.rbac import get_scoped_or_404, scoped_query
from app.db import get_db

router = APIRouter(prefix="/country-stats", tags=["command_view"])


@router.get("", response_model=list[CountryStatsRead])
def list_country_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Same scoped_query() helper used by cases/router.py - zero new RBAC
    # code needed for a second, structurally different entity.
    return scoped_query(db, CountryStats, user).all()


@router.get("/{country}", response_model=CountryStatsRead)
def get_country_stats(country: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stats = (
        scoped_query(db, CountryStats, user).filter(CountryStats.country == country).first()
    )
    if stats is None:
        raise HTTPException(status_code=404, detail="No stats for this country")
    return stats
