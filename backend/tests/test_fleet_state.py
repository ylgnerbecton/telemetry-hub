from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vehicle
from app.domain.enums import VehicleStatus


async def _seed_vehicles(session: AsyncSession, counts: dict[str, int]) -> None:
    now = datetime.now(timezone.utc)
    index = 0
    for status, amount in counts.items():
        for _ in range(amount):
            index += 1
            session.add(
                Vehicle(
                    vehicle_id=f"v-{index:02d}",
                    current_status=status,
                    battery_pct=50,
                    speed_mps=0.0,
                    lat=0.0,
                    lon=0.0,
                    last_seen_at=now,
                    updated_at=now,
                )
            )
    await session.commit()


async def test_fleet_state_groups_counts_by_status(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_vehicles(
        session,
        {
            VehicleStatus.IDLE.value: 3,
            VehicleStatus.MOVING.value: 5,
            VehicleStatus.CHARGING.value: 2,
            VehicleStatus.FAULT.value: 1,
        },
    )

    response = await client.get("/fleet/state")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 11
    assert body["by_status"] == {"idle": 3, "moving": 5, "charging": 2, "fault": 1}
    assert body["generated_at"]


async def test_fleet_state_with_no_vehicles_returns_zeros(client: AsyncClient) -> None:
    response = await client.get("/fleet/state")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["by_status"] == {"idle": 0, "moving": 0, "charging": 0, "fault": 0}
