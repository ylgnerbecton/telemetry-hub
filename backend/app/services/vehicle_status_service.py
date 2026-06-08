import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import VehicleStatus
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.mission_repository import MissionRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicles import VehicleStatusUpdateResponse

_FAULT_REASON: Final = "Vehicle entered fault status"


class VehicleNotFoundError(Exception):
    def __init__(self, vehicle_id: str) -> None:
        super().__init__(f"vehicle not found: {vehicle_id}")
        self.vehicle_id = vehicle_id


@dataclass(frozen=True)
class FaultTransitionResult:
    mission_cancelled: bool
    maintenance_record_created: bool


class VehicleStatusService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._vehicles = VehicleRepository(session)
        self._missions = MissionRepository(session)
        self._maintenance = MaintenanceRepository(session)

    async def transition_to_fault(self, vehicle_id: str, *, now: datetime) -> FaultTransitionResult:
        vehicle = await self._vehicles.get_for_update(vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError(vehicle_id)
        vehicle.current_status = VehicleStatus.FAULT.value
        vehicle.updated_at = now

        cancelled_mission_id: uuid.UUID | None = None
        mission_cancelled = False
        active_mission = await self._missions.get_active_for_update(vehicle_id)
        if active_mission is not None:
            await self._missions.cancel(active_mission, cancelled_at=now, reason=_FAULT_REASON)
            cancelled_mission_id = active_mission.id
            mission_cancelled = True

        maintenance_created = False
        open_record = await self._maintenance.get_open_for_update(vehicle_id)
        if open_record is None:
            await self._maintenance.create(
                vehicle_id=vehicle_id,
                mission_id=cancelled_mission_id,
                reason=_FAULT_REASON,
                created_at=now,
            )
            maintenance_created = True

        return FaultTransitionResult(
            mission_cancelled=mission_cancelled,
            maintenance_record_created=maintenance_created,
        )

    async def update_status(self, vehicle_id: str, new_status: VehicleStatus) -> VehicleStatusUpdateResponse:
        now = datetime.now(timezone.utc)
        async with self._session.begin():
            if new_status == VehicleStatus.FAULT:
                result = await self.transition_to_fault(vehicle_id, now=now)
                return VehicleStatusUpdateResponse(
                    vehicle_id=vehicle_id,
                    status=new_status,
                    mission_cancelled=result.mission_cancelled,
                    maintenance_record_created=result.maintenance_record_created,
                )

            vehicle = await self._vehicles.get_for_update(vehicle_id)
            if vehicle is None:
                raise VehicleNotFoundError(vehicle_id)
            vehicle.current_status = new_status.value
            vehicle.updated_at = now
            return VehicleStatusUpdateResponse(
                vehicle_id=vehicle_id,
                status=new_status,
                mission_cancelled=False,
                maintenance_record_created=False,
            )
