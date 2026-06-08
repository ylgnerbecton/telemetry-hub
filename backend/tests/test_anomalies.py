from datetime import datetime, timedelta, timezone

from helpers import make_telemetry_payload
from httpx import AsyncClient


async def _anomaly_types(client: AsyncClient, vehicle_id: str) -> set[str]:
    response = await client.get("/anomalies", params={"vehicle_id": vehicle_id})
    assert response.status_code == 200
    return {anomaly["type"] for anomaly in response.json()["items"]}


async def test_low_battery_creates_high_severity_anomaly(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-01", battery_pct=10))

    response = await client.get("/anomalies", params={"vehicle_id": "v-01"})
    items = response.json()["items"]
    low_battery = next(anomaly for anomaly in items if anomaly["type"] == "low_battery")
    assert low_battery["severity"] == "high"
    assert low_battery["metadata"]["battery_pct"] == 10


async def test_fault_status_creates_critical_anomaly(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-02", status="fault"))
    assert "fault_status" in await _anomaly_types(client, "v-02")


async def test_error_codes_create_anomaly(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-03", error_codes=["E_MOTOR"]))
    assert "error_code" in await _anomaly_types(client, "v-03")


async def test_overspeed_creates_anomaly(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-04", speed_mps=9.0))
    assert "overspeed" in await _anomaly_types(client, "v-04")


async def test_stale_timestamp_creates_anomaly(client: AsyncClient) -> None:
    stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-05", timestamp=stale))
    assert "stale_timestamp" in await _anomaly_types(client, "v-05")


async def test_anomalies_filtered_by_vehicle(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-06", battery_pct=5))
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-07", battery_pct=5))

    response = await client.get("/anomalies", params={"vehicle_id": "v-06"})
    vehicles = {anomaly["vehicle_id"] for anomaly in response.json()["items"]}
    assert vehicles == {"v-06"}


async def test_anomalies_filtered_by_time_range(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-08", battery_pct=5))

    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    empty = await client.get("/anomalies", params={"vehicle_id": "v-08", "from": future})
    assert empty.json()["items"] == []

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    present = await client.get("/anomalies", params={"vehicle_id": "v-08", "from": past})
    assert len(present.json()["items"]) >= 1


async def test_pagination_covers_all_items_without_overlap(client: AsyncClient) -> None:
    total = 25
    page_size = 10
    for _ in range(total):
        await client.post("/telemetry", json=make_telemetry_payload(vehicle_id="v-50", battery_pct=5))

    collected: list[dict[str, str]] = []
    cursor: str | None = None
    pages = 0
    while True:
        params: dict[str, object] = {"vehicle_id": "v-50", "limit": page_size}
        if cursor is not None:
            params["cursor"] = cursor
        body = (await client.get("/anomalies", params=params)).json()
        collected.extend(body["items"])
        pages += 1
        if not body["has_more"]:
            assert body["next_cursor"] is None
            break
        cursor = body["next_cursor"]
        assert cursor is not None
        assert pages < total

    ids = [anomaly["id"] for anomaly in collected]
    assert len(ids) == total
    assert len(set(ids)) == total
    observed_at_values = [anomaly["observed_at"] for anomaly in collected]
    assert observed_at_values == sorted(observed_at_values, reverse=True)


async def test_invalid_cursor_returns_400(client: AsyncClient) -> None:
    response = await client.get("/anomalies", params={"cursor": "not-a-valid-cursor"})
    assert response.status_code == 400
