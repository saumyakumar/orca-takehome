from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit_logs.router import router as audit_logs_router
from app.auth.fake_users import User
from app.cases.router import router as cases_router
from app.command_view.router import router as command_view_router
from app.core.deps import get_current_user
from app.core.events import EVENT_BUS, CaseClosed
from app.command_view.service import on_case_closed
from app.notifications.router import router as notifications_router
from app.db import Base, engine

# Import every model module so Base.metadata knows about all tables
# before create_all() runs.
from app.cases import models as _cases_models  # noqa: F401
from app.command_view import models as _command_view_models  # noqa: F401
from app.core import audit as _audit_models  # noqa: F401
from app.core import notifications as _notifications_models  # noqa: F401
from app.localization import models as _localization_models  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Wiring, not app logic: cases/ never imports command_view/ directly -
    # this is the only place that connects the two, and it's generic
    # enough that a third app could subscribe to CaseClosed the same way.
    EVENT_BUS.subscribe(CaseClosed, on_case_closed)
    yield


app = FastAPI(title="ORCA Platform Foundation", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)
app.include_router(command_view_router)
app.include_router(audit_logs_router)
app.include_router(notifications_router)


@app.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "role": user.role, "country": user.country}
