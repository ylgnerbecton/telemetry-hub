# Architecture Decision Record

Status: accepted. Context: Telemetry Hub, a 5-to-6 hour vertical slice of a fleet telemetry
monitoring service for 50 autonomous vehicles at about 1 Hz.

## 1. Most important decisions

### PostgreSQL with database-level concurrency control

The defining requirements are "no lost zone increments under concurrent writes" and "atomic
fault transition". Both are concurrency problems, so the database is the right place to solve
them, not application code.

- Zone counters increment with a single statement:
  `INSERT INTO zone_counters (...) VALUES (...) ON CONFLICT (zone_id) DO UPDATE SET
  entry_count = zone_counters.entry_count + 1`. The increment happens inside the database, so
  there is no read-modify-write window in Python where a concurrent request could overwrite a
  value. A test fires 100 concurrent events at one zone and asserts the count is exactly 100.
- The fault transition locks the vehicle row with `SELECT ... FOR UPDATE`, then cancels the
  active mission and opens a maintenance record, all in one transaction. Concurrent fault
  requests for the same vehicle serialize on that row lock. Partial unique indexes,
  `unique(vehicle_id) where status = 'active'` and `unique(vehicle_id) where status = 'open'`,
  are a database-level guarantee that duplicates are impossible even if the application logic
  were wrong. A test fires concurrent fault updates and asserts exactly one cancellation and
  one open maintenance record.

SQLite was rejected: its single-writer lock would serialize everything and mask concurrency
behavior rather than demonstrate correctness, and it cannot express partial unique indexes.

### Single-transaction ingestion with one fault code path

`POST /telemetry` does everything in one transaction and commits once: upsert the vehicle,
insert the event, increment the zone counter, detect and insert anomalies, and, if the status
is fault, run the fault transition. Either the whole event lands or none of it does, so the
system never holds partial telemetry state. Crucially, telemetry that reports fault calls the
same `VehicleStatusService.transition_to_fault` that the status endpoint uses, so the
mission-cancellation and maintenance logic lives in exactly one place.

### Polling over WebSockets, simple deterministic anomalies

The dashboard polls with TanStack Query (one to two second intervals). At this scale that is
simpler and more robust than WebSockets, with no connection lifecycle to manage. Anomaly
detection is five deterministic threshold rules (fault status, low battery, error codes,
overspeed, stale timestamp). They are explainable, testable, and free of false-precision; the
thresholds are configuration, not magic numbers, so they can be tuned without code changes.

### Keyset pagination for the anomaly stream

The anomaly table is the only collection that grows without bound, so `GET /anomalies` is
cursor-paginated with keyset pagination ordered by `(observed_at, id)`. Keyset avoids the
`OFFSET` scan cost that degrades as the table grows and is stable under concurrent inserts.
The response is a generic `PaginatedResponse[T]` envelope (`items`, `next_cursor`,
`has_more`) and the dashboard consumes it with TanStack Query's `useInfiniteQuery`. The
bounded collections (50 vehicles, 20 zones) are returned whole, since paginating fixed-size
sets adds machinery without value. The dashboard UI uses MUI (Material UI) for a consistent,
accessible component set.

## 2. Unclear requirements and assumptions

- No event identifier is provided by the edge client, so every accepted `POST /telemetry` is
  treated as a distinct event. There is no ingestion idempotency key.
- Zone geometry is out of scope; the edge client is trusted to set `zone_entered`. Unknown
  zones are rejected with 422 rather than silently counted.
- Authentication is out of scope. CORS is still restricted to the configured frontend origin.
- The vehicle clock may be stale, so `vehicle_timestamp` and server `received_at` are stored
  separately, and anomaly observation time uses the server clock.
- Fault from telemetry must behave identically to an explicit status change, so both share one
  service method.
- 50 vehicles at 1 Hz is about 50 writes per second, which a single PostgreSQL handles
  comfortably, so fleet state is computed live with a `GROUP BY` rather than maintained in a
  counter table.
- There is no recovery workflow defined for leaving fault, so none is implemented; fault side
  effects persist until an operator acts.

## 3. What would change at significant scale

"Significant" here means thousands of vehicles, 10k or more events per second, multiple
warehouses, strict real-time UI, or long-term analytics. In that world:

- Ingestion moves behind a streaming log (Kafka or Redpanda); the API becomes a thin producer
  and anomaly detection plus state updates become consumers, smoothing bursts.
- Telemetry storage becomes time-partitioned or moves to TimescaleDB, with retention and
  continuous aggregates.
- Fleet aggregates stop being computed per request; they become a cached or materialized view,
  or a maintained counter updated transactionally.
- The UI moves to WebSockets or Server-Sent Events for push updates instead of polling.
- Anomaly processing moves to background workers, with an outbox pattern so detection is
  decoupled from the ingestion transaction while staying exactly-once.
- A full observability stack (OpenTelemetry traces, Prometheus metrics, dashboards) and
  authentication and authorization are added.

## 4. Deliberately left out

Authentication, zone geometry, machine-learning or statistical anomaly detection, complex
mission planning, WebSockets, Kafka, Redis, background workers, and production deployment
infrastructure (Kubernetes, Terraform). Each is either explicitly out of scope or a scale
concern that would be premature for a 50-vehicle slice, and including them would trade
correctness and clarity for unused machinery. Observability (tracing and metrics) was also
left out of v1 for the same reason and is listed above as the first thing to add.
