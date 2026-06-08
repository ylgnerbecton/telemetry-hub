from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FleetStatusCounts(BaseModel):
    model_config = ConfigDict(frozen=True)

    idle: int = 0
    moving: int = 0
    charging: int = 0
    fault: int = 0


class FleetStateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    by_status: FleetStatusCounts
    generated_at: datetime
