from datetime import datetime, timezone
from typing import Any


def make_telemetry_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "vehicle_id": "v-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": 37.41,
        "lon": -122.08,
        "battery_pct": 80,
        "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }
    payload.update(overrides)
    return payload
