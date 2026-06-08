import asyncio
import random
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.domain.zones import ZONES

VEHICLE_COUNT = 50
TICK_SECONDS = 1.0
ZONE_ENTRY_PROBABILITY = 0.15
FAULT_PROBABILITY = 0.01
ERROR_PROBABILITY = 0.03
LOW_BATTERY_PROBABILITY = 0.05
OVERSPEED_PROBABILITY = 0.05
MOVING_STATUSES = ("idle", "moving", "charging")
ERROR_CODE_SAMPLES = ("E_SENSOR", "E_MOTOR", "E_NAV")
REQUEST_TIMEOUT_SECONDS = 10.0

logger = get_logger()


def _build_event(vehicle_id: str) -> dict[str, Any]:
    status = "fault" if random.random() < FAULT_PROBABILITY else random.choice(MOVING_STATUSES)

    battery_pct = random.randint(0, 14) if random.random() < LOW_BATTERY_PROBABILITY else random.randint(20, 100)

    speed_mps = round(random.uniform(0.5, 3.0), 2) if status == "moving" else 0.0
    if status == "moving" and random.random() < OVERSPEED_PROBABILITY:
        speed_mps = round(random.uniform(5.1, 9.0), 2)

    error_codes = [random.choice(ERROR_CODE_SAMPLES)] if random.random() < ERROR_PROBABILITY else []
    zone_entered = random.choice(ZONES) if random.random() < ZONE_ENTRY_PROBABILITY else None

    return {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": round(random.uniform(37.40, 37.42), 5),
        "lon": round(random.uniform(-122.09, -122.07), 5),
        "battery_pct": battery_pct,
        "speed_mps": speed_mps,
        "status": status,
        "error_codes": error_codes,
        "zone_entered": zone_entered,
    }


async def _send_tick(client: httpx.AsyncClient, vehicle_ids: list[str]) -> None:
    events = [_build_event(vehicle_id) for vehicle_id in vehicle_ids]
    responses = await asyncio.gather(
        *(client.post("/telemetry", json=event) for event in events),
        return_exceptions=True,
    )
    accepted = 0
    for response in responses:
        if isinstance(response, httpx.Response) and response.status_code == 201:
            accepted += 1
    logger.info("simulate.tick", accepted=accepted, total=len(events))


async def _run(base_url: str) -> None:
    vehicle_ids = [f"v-{index:02d}" for index in range(1, VEHICLE_COUNT + 1)]
    logger.info("simulate.start", target=base_url, vehicles=VEHICLE_COUNT)
    async with httpx.AsyncClient(base_url=base_url, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        loop = asyncio.get_running_loop()
        while True:
            started = loop.time()
            await _send_tick(client, vehicle_ids)
            elapsed = loop.time() - started
            await asyncio.sleep(max(0.0, TICK_SECONDS - elapsed))


def main() -> None:
    configure_logging()
    settings = get_settings()
    try:
        asyncio.run(_run(settings.simulator_target_url))
    except KeyboardInterrupt:
        logger.info("simulate.stopped")


if __name__ == "__main__":
    main()
