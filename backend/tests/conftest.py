import os
import pathlib

TEST_DB_PATH = pathlib.Path(__file__).parent / "test_orca.db"
os.environ["ORCA_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

import pytest
from fastapi.testclient import TestClient

# Import every model module before create_all(), same as app/main.py does.
from app.cases import models as _cases_models  # noqa: F401
from app.command_view import models as _command_view_models  # noqa: F401
from app.core import audit as _audit_models  # noqa: F401
from app.core import notifications as _notifications_models  # noqa: F401
from app.localization import models as _localization_models  # noqa: F401
from app.db import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def auth_headers(user_id: str) -> dict:
    return {"X-User-Id": user_id}
