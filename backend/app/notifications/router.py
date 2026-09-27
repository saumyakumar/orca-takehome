from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.fake_users import User
from app.core.deps import get_current_user
from app.core.notifications import Notification, NotificationRead
from app.db import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Owner-scoped, not country-scoped (see core/notifications.py) - a
    # notification is only ever visible to the user it was addressed to.
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == user.id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .all()
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.recipient_id == user.id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.recipient_id == user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
