import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import VehicleStatus
from app.domain.zones import ZONE_SET


class TelemetryIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str = Field(min_length=1, max_length=50)
    timestamp: datetime
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    battery_pct: int = Field(ge=0, le=100)
    speed_mps: float = Field(ge=0)
    status: VehicleStatus
    error_codes: list[str] = Field(default_factory=list)
    zone_entered: str | None = None

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("zone_entered")
    @classmethod
    def ensure_known_zone(cls, value: str | None) -> str | None:
        if value is not None and value not in ZONE_SET:
            raise ValueError(f"unknown zone: {value}")
        return value


class TelemetryIngestResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: uuid.UUID
    vehicle_id: str
    anomalies_created: int
    zone_count_incremented: bool
    zone_entered: str | None = None
