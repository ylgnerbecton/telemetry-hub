from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.anomaly_repository import AnomalyRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.anomalies import AnomalyBrief
from app.schemas.vehicles import VehicleRead, VehiclesResponse


class VehicleReadService:
    def __init__(self, session: AsyncSession) -> None:
        self._vehicles = VehicleRepository(session)
        self._anomalies = AnomalyRepository(session)

    async def list_vehicles(self) -> VehiclesResponse:
        vehicles = await self._vehicles.list_all()
        latest_by_vehicle = await self._anomalies.most_recent_by_vehicle()
        items = [
            VehicleRead(
                vehicle_id=vehicle.vehicle_id,
                current_status=vehicle.current_status,
                battery_pct=vehicle.battery_pct,
                speed_mps=vehicle.speed_mps,
                lat=vehicle.lat,
                lon=vehicle.lon,
                last_seen_at=vehicle.last_seen_at,
                most_recent_anomaly=(
                    AnomalyBrief.model_validate(latest_by_vehicle[vehicle.vehicle_id])
                    if vehicle.vehicle_id in latest_by_vehicle
                    else None
                ),
            )
            for vehicle in vehicles
        ]
        return VehiclesResponse(vehicles=items)
