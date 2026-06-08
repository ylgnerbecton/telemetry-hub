from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import VehicleStatus
from app.schemas.anomalies import AnomalyBrief


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    vehicle_id: str
    current_status: VehicleStatus
    battery_pct: int | None
    speed_mps: float | None
    lat: float | None
    lon: float | None
    last_seen_at: datetime | None
    most_recent_anomaly: AnomalyBrief | None = None


class VehiclesResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    vehicles: list[VehicleRead]


class VehicleStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: VehicleStatus


class VehicleStatusUpdateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    vehicle_id: str
    status: VehicleStatus
    mission_cancelled: bool
    maintenance_record_created: bool
