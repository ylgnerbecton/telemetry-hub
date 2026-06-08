import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.logging import configure_logging, get_logger
from app.db.models import Mission, Vehicle, ZoneCounter
from app.db.session import engine, session_factory
from app.domain.enums import MissionStatus, VehicleStatus
from app.domain.zones import ZONES

VEHICLE_COUNT = 50
BASE_LAT = 37.41
BASE_LON = -122.08

logger = get_logger()


async def _seed() -> None:
    now = datetime.now(timezone.utc)
    vehicle_ids = [f"v-{index:02d}" for index in range(1, VEHICLE_COUNT + 1)]

    async with session_factory() as session, session.begin():
        for vehicle_id in vehicle_ids:
            await session.execute(
                insert(Vehicle)
                .values(
                    vehicle_id=vehicle_id,
                    current_status=VehicleStatus.IDLE.value,
                    battery_pct=100,
                    speed_mps=0.0,
                    lat=BASE_LAT,
                    lon=BASE_LON,
                    last_seen_at=now,
                    updated_at=now,
                )
                .on_conflict_do_nothing(index_elements=["vehicle_id"])
            )

        for zone_id in ZONES:
            await session.execute(
                insert(ZoneCounter).values(zone_id=zone_id).on_conflict_do_nothing(index_elements=["zone_id"])
            )

        active = await session.execute(select(Mission.vehicle_id).where(Mission.status == MissionStatus.ACTIVE.value))
        vehicles_with_active_mission = {row[0] for row in active.all()}
        for vehicle_id in vehicle_ids:
            if vehicle_id not in vehicles_with_active_mission:
                session.add(
                    Mission(
                        vehicle_id=vehicle_id,
                        status=MissionStatus.ACTIVE.value,
                        started_at=now,
                    )
                )

    await engine.dispose()
    logger.info("seed.completed", vehicles=VEHICLE_COUNT, zones=len(ZONES))


def main() -> None:
    configure_logging()
    asyncio.run(_seed())


if __name__ == "__main__":
    main()
