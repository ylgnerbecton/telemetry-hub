from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ZoneCountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    zone_id: str
    entry_count: int
    updated_at: datetime


class ZonesResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    zones: list[ZoneCountRead]
