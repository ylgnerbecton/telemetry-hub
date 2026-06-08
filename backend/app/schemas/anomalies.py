import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AnomalySeverity, AnomalyType


class AnomalyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    type: AnomalyType
    severity: AnomalySeverity
    message: str
    observed_at: datetime


class AnomalyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True, populate_by_name=True)

    id: uuid.UUID
    vehicle_id: str
    type: AnomalyType
    severity: AnomalySeverity
    message: str
    observed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="context")
