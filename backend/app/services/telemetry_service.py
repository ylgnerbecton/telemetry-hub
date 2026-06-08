from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import Anomaly
from app.domain.enums import VehicleStatus
from app.repositories.anomaly_repository import AnomalyRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.zone_repository import ZoneRepository
from app.schemas.telemetry import TelemetryIngest, TelemetryIngestResponse
from app.services.anomaly_service import AnomalyService
from app.services.vehicle_status_service import VehicleStatusService


class TelemetryService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._vehicles = VehicleRepository(session)
        self._telemetry = TelemetryRepository(session)
        self._zones = ZoneRepository(session)
        self._anomalies = AnomalyRepository(session)
        self._anomaly_service = AnomalyService(session, settings)
        self._fault_service = VehicleStatusService(session)

    async def ingest(self, payload: TelemetryIngest) -> TelemetryIngestResponse:
        received_at = datetime.now(timezone.utc)
        async with self._session.begin():
            await self._vehicles.upsert_state(
                vehicle_id=payload.vehicle_id,
                status=payload.status.value,
                battery_pct=payload.battery_pct,
                speed_mps=payload.speed_mps,
                lat=payload.lat,
                lon=payload.lon,
                last_seen_at=received_at,
                updated_at=received_at,
            )
            event = await self._telemetry.insert(
                vehicle_id=payload.vehicle_id,
                vehicle_timestamp=payload.timestamp,
                received_at=received_at,
                lat=payload.lat,
                lon=payload.lon,
                battery_pct=payload.battery_pct,
                speed_mps=payload.speed_mps,
                status=payload.status.value,
                error_codes=payload.error_codes,
                zone_entered=payload.zone_entered,
            )

            zone_count_incremented = False
            if payload.zone_entered is not None:
                await self._zones.increment(payload.zone_entered, updated_at=received_at)
                zone_count_incremented = True

            candidates = self._anomaly_service.detect(payload, received_at)
            anomaly_rows = [
                Anomaly(
                    vehicle_id=payload.vehicle_id,
                    telemetry_event_id=event.id,
                    type=candidate.type.value,
                    severity=candidate.severity.value,
                    message=candidate.message,
                    observed_at=received_at,
                    context=candidate.context,
                )
                for candidate in candidates
            ]
            if anomaly_rows:
                self._anomalies.add_many(anomaly_rows)

            if payload.status == VehicleStatus.FAULT:
                await self._fault_service.transition_to_fault(payload.vehicle_id, now=received_at)

        return TelemetryIngestResponse(
            event_id=event.id,
            vehicle_id=payload.vehicle_id,
            anomalies_created=len(anomaly_rows),
            zone_count_incremented=zone_count_incremented,
            zone_entered=payload.zone_entered,
        )
