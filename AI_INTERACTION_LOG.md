# AI Interaction Log

This project was built in a single session by an AI coding agent (Claude, via Claude Code).
This log records the meaningful prompts, what the agent produced, the corrections that were
needed, and an honest reflection. Nothing here is fabricated; every correction below is a
problem that actually came up during the build and was fixed.

## Initial prompt

Summarized: build Telemetry Hub, a professional vertical slice of a fleet telemetry service
for 50 autonomous vehicles at 1 Hz, per the detailed `INSTRUCTIONS.md` and `PROJECT.md`.
Stack fixed as FastAPI + PostgreSQL + SQLAlchemy async on the backend and React + TypeScript
+ Vite + TanStack Query on the frontend, with polling rather than WebSockets. Deliverables
include the backend, dashboard, tests, Docker Compose, README, ADR, and this log. The agent
was also asked to follow a strict house style (no comments, English identifiers, no magic
numbers, typed everything) and to publish the result as a public GitHub repository.

## Phase 1: planning

The agent inspected the two specification files and the local environment (confirming git,
the GitHub CLI auth, Python, Node, and a running Docker daemon), wrote `docs/PLAN.md`, and
wrote `AGENTS.md` reconciling the strict house style with this external assessment. Output:
a build order prioritizing concurrency correctness, and an explicit, documented set of
deviations (no auth, no OpenTelemetry or Prometheus in v1, response shapes following the spec
rather than a generic envelope).

## Phase 2 and 3: backend architecture, schema, and concurrency

The agent generated the layered backend (domain, schemas, repositories, services, routes),
SQLAlchemy 2.0 models, and a hand-written Alembic migration including the two partial unique
indexes and the telemetry check constraints, plus the 20-zone data seed.

Key concurrency decisions the agent made and then double-checked by writing tests that
actually exercise them against PostgreSQL:

- Zone counter increments use `INSERT ... ON CONFLICT DO UPDATE SET entry_count =
  zone_counters.entry_count + 1`, never read-modify-write in Python.
- The fault transition locks the vehicle row with `SELECT ... FOR UPDATE` and relies on
  partial unique indexes as a backstop.
- Telemetry ingestion is one transaction, and a fault status reuses the same service method
  as the status endpoint.

Correction made: the `metadata` column name collides with SQLAlchemy's reserved Declarative
attribute. The agent mapped the ORM attribute `context` to the `metadata` column and exposed
it as `metadata` in the API through a Pydantic validation alias.

## Phase 4: tests, and the real bug found

The agent wrote 21 tests and ran them against a real PostgreSQL. The first full run had 4
failures, all in the fault transition tests, with a foreign-key violation when inserting a
`Mission` for a freshly added `Vehicle`.

Root cause the agent diagnosed: without an ORM relationship between `Mission` and `Vehicle`,
SQLAlchemy's unit of work does not order the two inserts within a single flush, so the mission
was sometimes inserted before its vehicle. The application code was never affected because it
sequences its writes explicitly; only the test seed helper batched both objects. Fix: flush
the vehicle before adding the mission in the test helper. The re-run was 21 of 21 passing.

The agent also verified the migration end to end: `alembic upgrade head`, confirm the 20
zones and both partial unique indexes, `alembic downgrade base`, then `upgrade head` again.

## Phase 5: frontend

The agent generated the Vite + React + TypeScript dashboard with TanStack Query polling hooks,
typed API client and models, and the four panels plus a health indicator, then verified a
strict `tsc` type-check and `vite build`. It ran the full stack live (backend, simulator,
frontend) and captured a screenshot showing real data flowing through the dashboard.

## Phase 6 and 7: scripts and infrastructure

The agent wrote the seed and simulator scripts and ran them against the live backend,
confirming all 20 zones counting, all four runtime anomaly types being produced, and fleet
state shifting. It wrote the Dockerfiles, Makefile, and Compose file, then built the images
and brought the whole stack up to confirm it works, including seeding inside the container.

Corrections made during verification, driven by the development machine already running an
unrelated stack on ports 5432, 5173, and 5174:

- The agent kept the committed defaults spec-compliant (5432, 8000, 5173) but made the Compose
  host ports configurable via environment variables so the stack does not collide on a busy
  machine, and ran its own verification on alternate ports.
- The agent broadened the backend CORS setting to accept a comma-separated list of origins,
  which was needed to screenshot the dashboard on a non-default port and is generally useful.
- For the test run it used a throwaway PostgreSQL container on a free port rather than
  disturbing the machine's existing database.

## Follow-up iteration: MUI, pagination, screenshots

A second prompt asked to raise the bar: use MUI on the frontend, add real pagination, keep
every test and guarantee green, and produce a worthy README with Swagger and dashboard
images, all following best practices.

The agent implemented keyset (cursor) pagination for `GET /anomalies`: a generic
`PaginatedResponse[T]` envelope, a base64 cursor codec, a repository query using a row-value
comparison on `(observed_at, id)` ordered newest first, and a service that fetches `limit + 1`
rows to compute `has_more`. It rebuilt the frontend with MUI (theme, AppBar, cards, table with
status chips and battery progress bars, zone bars, and an anomaly panel that consumes the
cursor pages with TanStack Query's `useInfiniteQuery` plus a Load older button). It added two
pagination tests (full traversal without overlap, and a malformed cursor returning 400),
bringing the suite to 23, all passing.

Corrections made during this iteration:

- A persistent formatting conflict: the editor's auto-formatter used a wider line length than
  the project's Ruff setting, so lines kept oscillating across the limit. The agent resolved it
  by aligning Ruff's line length to the formatter (120) instead of fighting it every edit.
- An invalid-cursor response initially used `HTTP_422_UNPROCESSABLE_ENTITY`, which is deprecated
  in the installed Starlette. The agent switched to `400 Bad Request`, which is both stable and
  a better fit for a malformed query parameter, and updated the test.
- MUI's `LinearProgress` rejects the `default` color, so the battery color helper's return type
  was narrowed to the three colors it actually returns.
- Headless Chrome (`--headless=new`) wrote the screenshots but did not exit, blocking a
  sequential capture. The agent switched to capturing against the built app via `vite preview`
  and added a poll-then-kill wrapper so each capture terminates deterministically. Both the
  dashboard and the Swagger UI (which shows the `PaginatedResponse[AnomalyRead]` schema) were
  captured to `docs/images/` and embedded in the README.

## Reflection

- Where AI helped most: scaffolding a consistent layered codebase quickly, writing the
  concurrency-correct SQL (atomic upsert, row locks, partial unique indexes) and the tests
  that prove it, and producing thorough documentation. The repetitive, pattern-heavy work
  (schemas, repositories, typed client) was fast and consistent.
- Where AI was risky or wrong: it initially wrote a test seed helper that relied on implicit
  insert ordering that SQLAlchemy does not guarantee without a relationship. The mistake was
  caught only because the tests were actually run against PostgreSQL, not assumed to pass.
- What needed manual review: transaction boundaries (ensuring the fault transition does not
  open its own transaction so it can be reused inside the ingestion transaction), and the
  `metadata` column collision, which would have been a silent runtime error.
- Concurrency assumptions that were double-checked: the 100-concurrent-events-to-one-zone test
  was run and asserted to equal exactly 100, and concurrent fault updates were asserted to
  produce exactly one mission cancellation and one open maintenance record. These were run,
  not reasoned about in the abstract.
- What would be improved with more time: an idempotency key for ingestion, a defined recovery
  path out of fault status, property-based tests for the anomaly rules, and a small load test
  to characterize ingestion throughput under sustained burst.
