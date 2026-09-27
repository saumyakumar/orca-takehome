from fastapi import Header, HTTPException

from app.auth.fake_users import FAKE_USERS, User


def get_current_user(x_user_id: str = Header(...)) -> User:
    user = FAKE_USERS.get(x_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown X-User-Id")
    return user
