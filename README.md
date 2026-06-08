# Telemetry Hub

[![CI](https://github.com/ylgnerbecton/telemetry-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/ylgnerbecton/telemetry-hub/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-minded vertical slice of a fleet telemetry monitoring service for 50 autonomous
industrial vehicles emitting telemetry at about 1 Hz. It ingests telemetry under concurrent
load, detects anomalies in real time, counts zone entries without losing increments,
transitions vehicles to fault atomically (cancelling the active mission and opening a
maintenance record), and surfaces everything through a live React dashboard.

This is a focused technical-assessment project, not a production deployment. Correctness
under concurrency and honest documentation were prioritized over breadth.

## Dashboard

The React + MUI dashboard polls the API and updates live. It shows the fleet status
breakdown, every vehicle with battery and most recent anomaly, live per-zone entry counts,
and a cursor-paginated stream of recent anomalies.

![Telemetry Hub dashboard](docs/images/dashboard.png)

Interactive API documentation (Swagger UI) is served at `/docs`.

![Swagger UI](docs/images/swagger.png)

## Architecture overview

The backend is a layered FastAPI service. Route handlers stay thin and delegate to services,
which own transaction boundaries; repositories hold all database access; the domain layer
holds enums, the fixed zone list, and the anomaly rules.

![Architecture](docs/images/architecture.png)

Telemetry ingestion is a single transaction (upsert the vehicle, insert the event, atomically
increment the zone counter, detect anomalies, and run the fault transition when the status is
fault), so an event lands whole or not at all:

![Telemetry ingestion transaction](docs/images/ingestion-sequence.png)

The fault transition is one row-locked service method shared by `POST /telemetry` and
`PATCH /vehicles/{id}/status`, with partial unique indexes as a backstop:

![Atomic fault transition](docs/images/fault-transition.png)

Diagram sources are in [docs/diagrams](docs/diagrams).

Layers (`backend/app`):

- `domain` enums, the 20 fixed zones, anomaly type-to-severity mapping.
- `schemas` Pydantic request and response models (the API contract).
- `repositories` database access only (SQLAlchemy 2.0 async).
- `services` use-case logic and transaction boundaries.
- `api/routes` thin HTTP handlers.

## Tech stack

- Backend: Python, FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, Pydantic v2,
  pydantic-settings, structlog.
- Database: PostgreSQL 16.
- Frontend: React 18, TypeScript, Vite, MUI (Material UI) v6, TanStack Query v5
  (cursor pagination via `useInfiniteQuery`).
- Tests: pytest, pytest-asyncio, httpx.
- Tooling: Ruff, Docker Compose, Makefile.

### Why PostgreSQL (not SQLite)

The hardest requirement is correct concurrent counting and atomic state transitions.
PostgreSQL gives real row-level locking (`SELECT ... FOR UPDATE`), atomic upserts
(`INSERT ... ON CONFLICT DO UPDATE`), and partial unique indexes. SQLite serializes writes
with a single database-level lock, which would hide concurrency bugs rather than prove
correctness, and it cannot express the partial unique constraints used here.

### Why FastAPI

The task is a focused, type-validated REST API. FastAPI gives Pydantic validation at the
boundary (invalid payloads return 422 automatically), first-class async I/O so concurrent
ingestion does not block, and generated OpenAPI docs at `/docs`.

### Why polling (not WebSockets)

At 50 vehicles and the dashboard's one-to-two second refresh, polling with TanStack Query is
simpler, has no connection-state edge cases, and is more than adequate. WebSockets or SSE
would be a scale improvement, not a current need. This is revisited in the ADR.

## Repository layout

```
telemetry-hub/
  backend/        FastAPI service, Alembic migrations, tests, seed and simulator scripts
  frontend/       React + TypeScript + Vite dashboard
  docs/           PLAN.md, ADR.md, images/
  docker-compose.yml, Makefile, .env.example
  README.md, AI_INTERACTION_LOG.md, AGENTS.md
```

## Quick start with Docker Compose

Requires Docker and Docker Compose.

```bash
cp .env.example .env
make up
docker compose exec backend python scripts/seed.py
make simulate
```

Then open the dashboard at http://localhost:5173 (API at http://localhost:8000, docs at
http://localhost:8000/docs).

`make up` builds and starts PostgreSQL, the backend (which runs `alembic upgrade head` on
start), and the frontend. `make simulate` runs the telemetry simulator from your host
against http://localhost:8000. Stop everything with `make down`.

If ports 5432, 8000, or 5173 are already in use, set `POSTGRES_HOST_PORT`,
`BACKEND_HOST_PORT`, or `FRONTEND_HOST_PORT` in `.env` before `make up`.

## Run the backend locally

Requires Python 3.10+ and a running PostgreSQL (use `docker compose up -d postgres`).

```bash
make backend-install        # python -m venv .venv && pip install -e ".[dev]"
make migrate                # alembic upgrade head
make seed                   # 50 vehicles, active missions, 20 zones
make backend-dev            # uvicorn on http://localhost:8000
```

The backend reads configuration from environment variables or a `.env` file (see
`.env.example`). `DATABASE_URL` defaults to the local Compose PostgreSQL.

## Run the frontend locally

Requires Node 18+.

```bash
make frontend-install
make frontend-dev           # http://localhost:5173
```

The dashboard calls the API at `VITE_API_BASE_URL` (default http://localhost:8000). It is
built with MUI, handles loading, error, and empty states for every panel, and pages through
anomaly history with a Load older control backed by cursor pagination.

## Seed data

```bash
# local
make seed
# inside the Compose stack
docker compose exec backend python scripts/seed.py
```

Seeding is idempotent: it creates vehicles `v-01` through `v-50`, one active mission per
vehicle, and ensures the 20 zone counter rows exist. The 20 zones are also inserted by the
initial migration, so the zone counts endpoint returns all 20 even before seeding.

## Run the simulator

```bash
make simulate
```

The simulator streams roughly one telemetry event per second per vehicle for all 50
vehicles, randomly varying battery, speed, status, and zone entries, and occasionally
producing low battery, error codes, overspeed, and fault events. It targets
`SIMULATOR_TARGET_URL` (default http://localhost:8000). Stop it with Ctrl+C.

## Run the tests

The suite runs against a real PostgreSQL. The test database (`telemetry_hub_test`) is created
automatically if it does not exist.

```bash
docker compose up -d postgres     # or: make up
make backend-install
make backend-test
```

The suite has 23 tests covering ingestion and validation, anomaly detection and filtering,
cursor pagination (full traversal without overlap, plus rejection of malformed cursors),
fleet aggregation, the zone counter concurrency guarantee (100 concurrent events to one zone
must produce exactly 100), and fault transition atomicity (including concurrent fault updates
producing no duplicate cancellations or maintenance records). All 23 pass.

`TEST_DATABASE_URL` controls the test database connection (default
`postgresql+asyncpg://telemetry:telemetry@localhost:5432/telemetry_hub_test`).

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness check, also verifies the database connection |
| POST | `/telemetry` | Ingest one telemetry event (validation, anomalies, zone counter, fault transition) |
| GET | `/vehicles` | Current state of all vehicles plus each vehicle's most recent anomaly |
| PATCH | `/vehicles/{vehicle_id}/status` | Update vehicle status; a fault transition is atomic |
| GET | `/fleet/state` | Vehicle counts grouped by status, plus total |
| GET | `/zones/counts` | Entry count for all 20 zones |
| GET | `/anomalies` | Recent anomalies (cursor-paginated); filters: `vehicle_id`, `from`, `to`, `limit`, `cursor` |

### Pagination

`GET /anomalies` uses keyset (cursor) pagination, which stays correct and fast as the table
grows because it never scans with `OFFSET`. The response is a generic envelope:

```json
{
  "items": [
    {
      "id": "019...",
      "vehicle_id": "v-12",
      "type": "low_battery",
      "severity": "high",
      "message": "Battery at 11% is below threshold 15%",
      "observed_at": "2026-06-08T03:49:10.123456+00:00",
      "metadata": { "battery_pct": 11 }
    }
  ],
  "next_cursor": "MjAyNi0wNi0wOFQwMzo0OToxMC4xMjM0NTYrMDA6MDB8MDE5...",
  "has_more": true
}
```

Results are ordered newest first by `(observed_at, id)`. Pass `next_cursor` back as the
`cursor` query parameter to fetch the next page; `has_more` is `false` and `next_cursor` is
`null` on the last page. A malformed cursor returns `400`. The dashboard consumes this with
TanStack Query's `useInfiniteQuery`.

## Concurrency guarantees

- Zone counters use a single atomic statement,
  `INSERT ... ON CONFLICT (zone_id) DO UPDATE SET entry_count = entry_count + 1`. There is no
  read-modify-write in Python, so concurrent entries to the same zone cannot lose increments.
  Proven by `test_zone_counter_concurrency.py` (100 concurrent events to one zone yield 100).
- Telemetry ingestion runs in one transaction and commits once. A failure rolls back the
  whole event, so no partial telemetry state is ever persisted.
- The fault transition locks the vehicle row with `SELECT ... FOR UPDATE` before touching the
  mission and maintenance record, serializing concurrent transitions for the same vehicle.
  Partial unique indexes (`unique(vehicle_id) where status = 'active'` and
  `... where status = 'open'`) are a database-level backstop against duplicate active missions
  or open maintenance records. Proven by `test_fault_transition_atomicity.py`.
- Telemetry arriving with `status == "fault"` calls the exact same fault transition service
  as the status endpoint, so the logic exists in one place.

## Anomaly rules

Detection is deterministic and intentionally simple (no machine learning). Thresholds are
configurable in `.env`.

| Condition | Type | Severity |
| --- | --- | --- |
| `status == "fault"` | `fault_status` | critical |
| `battery_pct < 15` | `low_battery` | high |
| `error_codes` not empty | `error_code` | medium |
| `speed_mps > 5.0` | `overspeed` | medium |
| telemetry timestamp more than 5 minutes older than server receipt | `stale_timestamp` | low |

The rationale is in [docs/ADR.md](docs/ADR.md).

## Configuration

All configuration is environment-driven (`.env`, see `.env.example`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://telemetry:telemetry@localhost:5432/telemetry_hub` | Backend database |
| `TEST_DATABASE_URL` | `...localhost:5432/telemetry_hub_test` | Test database |
| `API_HOST`, `API_PORT` | `0.0.0.0`, `8000` | Backend bind address |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed CORS origin(s), comma-separated |
| `LOW_BATTERY_THRESHOLD_PCT` | `15` | Low battery anomaly threshold |
| `OVERSPEED_THRESHOLD_MPS` | `5.0` | Overspeed anomaly threshold |
| `STALE_TELEMETRY_MAX_AGE_SECONDS` | `300` | Stale timestamp anomaly threshold |
| `SIMULATOR_TARGET_URL` | `http://localhost:8000` | Where the simulator sends events |
| `VITE_API_BASE_URL` | `http://localhost:8000` | API base URL used by the frontend |

## Known limitations

- No authentication or authorization (out of scope per the brief). CORS is restricted to the
  configured frontend origin.
- Zone geometry is not modeled. The edge client is trusted to set `zone_entered`; unknown
  zones are rejected with 422.
- Fleet state is computed live on every request. This is correct and cheap at 50 vehicles;
  the ADR describes when to cache or materialize it.
- The simulator picks a fresh random status each tick, so a vehicle that briefly reports
  fault may report a normal status on the next tick. The fault side effects (cancelled
  mission, open maintenance record) persist; there is deliberately no auto-recovery logic.
- The simulator sends current timestamps, so it does not produce `stale_timestamp` anomalies;
  that rule is covered by the test suite instead.
- Only the anomaly stream is paginated (cursor-based). The vehicles (50) and zones (20)
  endpoints return bounded, fixed-size collections, so paginating them would add no value.
- Tests require a running PostgreSQL; there is no SQLite fallback by design.

## Future improvements

See [docs/ADR.md](docs/ADR.md) for the full discussion. In short, at significantly larger
scale this would move toward a streaming ingestion log (Kafka or Redpanda), cached or
materialized fleet aggregates, partitioned or TimescaleDB telemetry storage, WebSockets or
SSE for the UI, background workers with an outbox for anomaly processing, a full
observability stack, and authentication.
