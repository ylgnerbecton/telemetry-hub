from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TelemetryEvent


class TelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(
        self,
        *,
        vehicle_id: str,
        vehicle_timestamp: datetime,
        received_at: datetime,
        lat: float,
        lon: float,
        battery_pct: int,
        speed_mps: float,
        status: str,
        error_codes: list[str],
        zone_entered: str | None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            vehicle_id=vehicle_id,
            vehicle_timestamp=vehicle_timestamp,
            received_at=received_at,
            lat=lat,
            lon=lon,
            battery_pct=battery_pct,
            speed_mps=speed_mps,
            status=status,
            error_codes=error_codes,
            zone_entered=zone_entered,
        )
        self._session.add(event)
        await self._session.flush()
        return event
