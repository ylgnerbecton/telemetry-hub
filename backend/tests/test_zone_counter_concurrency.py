import asyncio

from helpers import make_telemetry_payload
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ZoneCounter

CONCURRENT_EVENTS = 100
TARGET_ZONE = "charging_bay_1"


async def test_concurrent_events_same_zone_have_no_lost_increments(client: AsyncClient, session: AsyncSession) -> None:
    payloads = [
        make_telemetry_payload(vehicle_id=f"v-{index:03d}", zone_entered=TARGET_ZONE)
        for index in range(CONCURRENT_EVENTS)
    ]

    responses = await asyncio.gather(*(client.post("/telemetry", json=payload) for payload in payloads))

    assert all(response.status_code == 201 for response in responses)
    assert all(response.json()["zone_count_incremented"] is True for response in responses)

    count = (
        await session.execute(select(ZoneCounter.entry_count).where(ZoneCounter.zone_id == TARGET_ZONE))
    ).scalar_one()
    assert count == CONCURRENT_EVENTS


async def test_other_zones_remain_zero_after_targeted_burst(client: AsyncClient, session: AsyncSession) -> None:
    payloads = [make_telemetry_payload(vehicle_id=f"v-{index:03d}", zone_entered=TARGET_ZONE) for index in range(10)]
    await asyncio.gather(*(client.post("/telemetry", json=payload) for payload in payloads))

    untouched = (
        await session.execute(select(ZoneCounter.entry_count).where(ZoneCounter.zone_id == "aisle_a"))
    ).scalar_one()
    assert untouched == 0
