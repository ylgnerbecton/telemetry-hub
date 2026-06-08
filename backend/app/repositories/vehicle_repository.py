from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vehicle


class VehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_state(
        self,
        *,
        vehicle_id: str,
        status: str,
        battery_pct: int | None,
        speed_mps: float | None,
        lat: float | None,
        lon: float | None,
        last_seen_at: datetime,
        updated_at: datetime,
    ) -> None:
        stmt = insert(Vehicle).values(
            vehicle_id=vehicle_id,
            current_status=status,
            battery_pct=battery_pct,
            speed_mps=speed_mps,
            lat=lat,
            lon=lon,
            last_seen_at=last_seen_at,
            updated_at=updated_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["vehicle_id"],
            set_={
                "current_status": status,
                "battery_pct": battery_pct,
                "speed_mps": speed_mps,
                "lat": lat,
                "lon": lon,
                "last_seen_at": last_seen_at,
                "updated_at": updated_at,
            },
        )
        await self._session.execute(stmt)

    async def get(self, vehicle_id: str) -> Vehicle | None:
        stmt = select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self, vehicle_id: str) -> Vehicle | None:
        stmt = select(Vehicle).where(Vehicle.vehicle_id == vehicle_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Vehicle]:
        result = await self._session.execute(select(Vehicle).order_by(Vehicle.vehicle_id))
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Vehicle.current_status, func.count()).group_by(Vehicle.current_status)
        )
        return dict(result.all())
