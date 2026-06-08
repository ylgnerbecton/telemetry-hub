from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.pagination import CursorPosition, decode_cursor, encode_cursor
from app.domain.enums import (
    SEVERITY_BY_TYPE,
    AnomalySeverity,
    AnomalyType,
    VehicleStatus,
)
from app.repositories.anomaly_repository import AnomalyRepository
from app.schemas.anomalies import AnomalyRead
from app.schemas.pagination import PaginatedResponse
from app.schemas.telemetry import TelemetryIngest


@dataclass(frozen=True)
class AnomalyCandidate:
    type: AnomalyType
    severity: AnomalySeverity
    message: str
    context: dict[str, Any]


class AnomalyService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._settings = settings
        self._anomalies = AnomalyRepository(session)

    def detect(self, payload: TelemetryIngest, received_at: datetime) -> list[AnomalyCandidate]:
        candidates: list[AnomalyCandidate] = []

        if payload.status == VehicleStatus.FAULT:
            candidates.append(
                self._build(
                    AnomalyType.FAULT_STATUS,
                    "Vehicle reported fault status",
                    {"status": payload.status.value},
                )
            )

        if payload.battery_pct < self._settings.low_battery_threshold_pct:
            candidates.append(
                self._build(
                    AnomalyType.LOW_BATTERY,
                    f"Battery at {payload.battery_pct}% is below threshold {self._settings.low_battery_threshold_pct}%",
                    {"battery_pct": payload.battery_pct},
                )
            )

        if payload.error_codes:
            candidates.append(
                self._build(
                    AnomalyType.ERROR_CODE,
                    f"Vehicle reported error codes: {', '.join(payload.error_codes)}",
                    {"error_codes": payload.error_codes},
                )
            )

        if payload.speed_mps > self._settings.overspeed_threshold_mps:
            candidates.append(
                self._build(
                    AnomalyType.OVERSPEED,
                    f"Speed {payload.speed_mps} m/s exceeds limit {self._settings.overspeed_threshold_mps} m/s",
                    {"speed_mps": payload.speed_mps},
                )
            )

        age_seconds = (received_at - payload.timestamp).total_seconds()
        if age_seconds > self._settings.stale_telemetry_max_age_seconds:
            candidates.append(
                self._build(
                    AnomalyType.STALE_TIMESTAMP,
                    f"Telemetry timestamp is {int(age_seconds)}s older than server receipt",
                    {"age_seconds": int(age_seconds)},
                )
            )

        return candidates

    async def query(
        self,
        *,
        vehicle_id: str | None,
        time_from: datetime | None,
        time_to: datetime | None,
        cursor: str | None,
        limit: int,
    ) -> PaginatedResponse[AnomalyRead]:
        position = decode_cursor(cursor) if cursor else None
        rows = await self._anomalies.query(
            vehicle_id=vehicle_id,
            time_from=time_from,
            time_to=time_to,
            cursor=position,
            limit=limit + 1,
        )
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = encode_cursor(CursorPosition(observed_at=last.observed_at, anomaly_id=last.id))
        items = [AnomalyRead.model_validate(row) for row in page]
        return PaginatedResponse[AnomalyRead](items=items, next_cursor=next_cursor, has_more=has_more)

    def _build(self, anomaly_type: AnomalyType, message: str, context: dict[str, Any]) -> AnomalyCandidate:
        return AnomalyCandidate(
            type=anomaly_type,
            severity=SEVERITY_BY_TYPE[anomaly_type],
            message=message,
            context=context,
        )
