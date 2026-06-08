from helpers import make_telemetry_payload
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TelemetryEvent, Vehicle, ZoneCounter


async def test_valid_event_is_persisted_and_updates_vehicle(client: AsyncClient, session: AsyncSession) -> None:
    response = await client.post(
        "/telemetry",
        json=make_telemetry_payload(vehicle_id="v-07", battery_pct=64, status="moving"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["vehicle_id"] == "v-07"
    assert body["anomalies_created"] == 0
    assert body["zone_count_incremented"] is False
    assert body["event_id"]

    events = (await session.execute(select(TelemetryEvent).where(TelemetryEvent.vehicle_id == "v-07"))).scalars().all()
    assert len(events) == 1

    vehicle = (await session.execute(select(Vehicle).where(Vehicle.vehicle_id == "v-07"))).scalar_one()
    assert vehicle.current_status == "moving"
    assert vehicle.battery_pct == 64
    assert vehicle.last_seen_at is not None


async def test_invalid_battery_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_telemetry_payload(battery_pct=150))
    assert response.status_code == 422


async def test_invalid_status_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_telemetry_payload(status="flying"))
    assert response.status_code == 422


async def test_invalid_zone_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_telemetry_payload(zone_entered="nowhere"))
    assert response.status_code == 422


async def test_negative_speed_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_telemetry_payload(speed_mps=-1.0))
    assert response.status_code == 422


async def test_zone_increment_marks_response_and_counter(client: AsyncClient, session: AsyncSession) -> None:
    response = await client.post(
        "/telemetry",
        json=make_telemetry_payload(vehicle_id="v-09", zone_entered="charging_bay_1"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["zone_count_incremented"] is True
    assert body["zone_entered"] == "charging_bay_1"

    count = (
        await session.execute(select(ZoneCounter.entry_count).where(ZoneCounter.zone_id == "charging_bay_1"))
    ).scalar_one()
    assert count == 1
