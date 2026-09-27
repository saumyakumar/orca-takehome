from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    country: str
    owner_app: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    title: str
    description: Optional[str]
    status: str
    status_label: Optional[str] = None
    assigned_to: Optional[str]


class CaseListResponse(BaseModel):
    items: list[CaseRead]
    total: int
    limit: int
    offset: int
