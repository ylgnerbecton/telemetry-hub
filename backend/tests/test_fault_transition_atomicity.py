import asyncio
from datetime import datetime, timezone

from helpers import make_telemetry_payload
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MaintenanceRecord, Mission, Vehicle
from app.domain.enums import MaintenanceStatus, MissionStatus, VehicleStatus

CONCURRENT_FAULTS = 10


async def _seed_vehicle_with_active_mission(session: AsyncSession, vehicle_id: str) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        Vehicle(
            vehicle_id=vehicle_id,
            current_status=VehicleStatus.MOVING.value,
            battery_pct=70,
            speed_mps=1.0,
            lat=0.0,
            lon=0.0,
            last_seen_at=now,
            updated_at=now,
        )
    )
    await session.flush()
    session.add(Mission(vehicle_id=vehicle_id, status=MissionStatus.ACTIVE.value, started_at=now))
    await session.commit()


async def _count_missions(session: AsyncSession, vehicle_id: str, status: str) -> int:
    return (
        await session.execute(
            select(func.count()).select_from(Mission).where(Mission.vehicle_id == vehicle_id, Mission.status == status)
        )
    ).scalar_one()


async def _count_open_maintenance(session: AsyncSession, vehicle_id: str) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(MaintenanceRecord)
            .where(
                MaintenanceRecord.vehicle_id == vehicle_id,
                MaintenanceRecord.status == MaintenanceStatus.OPEN.value,
            )
        )
    ).scalar_one()


async def test_fault_patch_cancels_mission_and_creates_maintenance(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_vehicle_with_active_mission(session, "v-01")

    response = await client.patch("/vehicles/v-01/status", json={"status": "fault"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fault"
    assert body["mission_cancelled"] is True
    assert body["maintenance_record_created"] is True

    session.expire_all()
    vehicle = (await session.execute(select(Vehicle).where(Vehicle.vehicle_id == "v-01"))).scalar_one()
    assert vehicle.current_status == VehicleStatus.FAULT.value
    assert await _count_missions(session, "v-01", MissionStatus.CANCELLED.value) == 1
    assert await _count_missions(session, "v-01", MissionStatus.ACTIVE.value) == 0
    assert await _count_open_maintenance(session, "v-01") == 1


async def test_repeated_fault_is_idempotent(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_vehicle_with_active_mission(session, "v-02")

    first = await client.patch("/vehicles/v-02/status", json={"status": "fault"})
    second = await client.patch("/vehicles/v-02/status", json={"status": "fault"})

    assert first.json()["mission_cancelled"] is True
    assert first.json()["maintenance_record_created"] is True
    assert second.json()["mission_cancelled"] is False
    assert second.json()["maintenance_record_created"] is False
    assert await _count_missions(session, "v-02", MissionStatus.CANCELLED.value) == 1
    assert await _count_open_maintenance(session, "v-02") == 1


async def test_concurrent_fault_updates_create_no_duplicates(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_vehicle_with_active_mission(session, "v-03")

    responses = await asyncio.gather(
        *(client.patch("/vehicles/v-03/status", json={"status": "fault"}) for _ in range(CONCURRENT_FAULTS))
    )

    assert all(response.status_code == 200 for response in responses)
    assert sum(1 for response in responses if response.json()["mission_cancelled"]) == 1
    assert sum(1 for response in responses if response.json()["maintenance_record_created"]) == 1
    assert await _count_missions(session, "v-03", MissionStatus.CANCELLED.value) == 1
    assert await _count_open_maintenance(session, "v-03") == 1


async def test_telemetry_with_fault_status_triggers_transition(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_vehicle_with_active_mission(session, "v-04")

    response = await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-04", status="fault"))

    assert response.status_code == 201
    assert response.json()["anomalies_created"] >= 1

    session.expire_all()
    vehicle = (await session.execute(select(Vehicle).where(Vehicle.vehicle_id == "v-04"))).scalar_one()
    assert vehicle.current_status == VehicleStatus.FAULT.value
    assert await _count_missions(session, "v-04", MissionStatus.CANCELLED.value) == 1
    assert await _count_open_maintenance(session, "v-04") == 1
