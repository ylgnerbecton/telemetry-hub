from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import VehicleStatus
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.fleet import FleetStateResponse, FleetStatusCounts


class FleetStateService:
    def __init__(self, session: AsyncSession) -> None:
        self._vehicles = VehicleRepository(session)

    async def get_state(self) -> FleetStateResponse:
        counts = await self._vehicles.count_by_status()
        by_status = FleetStatusCounts(
            idle=counts.get(VehicleStatus.IDLE.value, 0),
            moving=counts.get(VehicleStatus.MOVING.value, 0),
            charging=counts.get(VehicleStatus.CHARGING.value, 0),
            fault=counts.get(VehicleStatus.FAULT.value, 0),
        )
        total = sum(counts.values())
        return FleetStateResponse(total=total, by_status=by_status, generated_at=datetime.now(timezone.utc))
