# Implementation Plan

Concise plan for the Telemetry Hub vertical slice. Time budget is roughly 5 to 6 hours,
so the plan prioritizes correctness under concurrency and honest documentation over breadth.

## Goal

A fleet telemetry monitoring service for 50 autonomous vehicles emitting at about 1 Hz:
ingest telemetry, detect anomalies, count zone entries without losing increments under
concurrency, transition vehicles to fault atomically, and surface fleet state, anomalies,
and zone counts through a small React dashboard.

## Build order

1. Foundation: config, logging, async SQLAlchemy session, ORM models, Alembic initial
   migration, FastAPI app, health endpoint.
2. Core backend: Pydantic schemas, repositories, services, routes.
   - Telemetry ingestion in a single transaction.
   - Atomic zone counter via `INSERT ... ON CONFLICT DO UPDATE`.
   - Fault transition via row locks (`SELECT ... FOR UPDATE`) plus partial unique indexes.
   - Fleet aggregate via a single `GROUP BY` over the vehicles table.
   - Anomalies query with optional vehicle and time-range filters.
3. Tests against a real PostgreSQL instance, including two concurrency tests.
4. Frontend dashboard with TanStack Query polling.
5. Seed and simulator scripts.
6. Docker Compose, Makefile, Dockerfiles.
7. Documentation: README, ADR, AI interaction log.
8. Verification: run tests, build frontend, lint, start Compose; then publish.

## Key design decisions

- PostgreSQL, not SQLite. Concurrent counter correctness and `SELECT ... FOR UPDATE`
  isolation need a real concurrent database.
- Zone counter increment is delegated to the database with a single atomic upsert. No
  read-modify-write in Python.
- The fault transition runs inside one transaction with the vehicle row locked first,
  then the active mission, then the maintenance record. Partial unique indexes make
  duplicate active missions and duplicate open maintenance records impossible.
- Telemetry that arrives with `status == "fault"` reuses the exact same fault transition
  use case as the explicit status endpoint. One source of truth.
- Polling, not WebSockets. Simpler and sufficient for 50 vehicles at 1 Hz.

## Risks and tradeoffs

- Concurrency tests need a live PostgreSQL and enough pool connections so that concurrent
  requests genuinely overlap. Mitigation: a dedicated test database and a connection pool
  sized above the concurrency used in tests.
- The `metadata` column name collides with SQLAlchemy's reserved Declarative attribute.
  Mitigation: the ORM attribute is `context`, mapped to the `metadata` column, and the API
  field is exposed as `metadata` through a Pydantic alias.
- Single-transaction ingestion couples several writes. If anomaly insertion or the fault
  transition fails, the whole event is rolled back. This is intentional: partial telemetry
  state is worse than a rejected event the edge client can retry.
- Fleet state is computed live on every request. Fine at this scale; documented in the ADR
  as the first thing to cache or materialize if scale grows.

## Out of scope (deliberate)

Authentication, zone geometry, machine-learning anomaly detection, WebSockets, Kafka,
Redis, background workers, and production deployment infrastructure. Rationale is in the ADR.
