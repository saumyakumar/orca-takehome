from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CountryStatsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    country: str
    open_case_count: int
    updated_at: datetime
