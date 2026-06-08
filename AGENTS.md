# AGENTS.md

Operating rules for AI agents and human contributors working in this repository.
This project is a focused technical-assessment vertical slice, not a production platform
service. These rules adapt a stricter house style to that reality.

## What this project is

Telemetry Hub: a fleet telemetry monitoring service for 50 autonomous industrial vehicles.
Backend is FastAPI plus SQLAlchemy 2.0 async on PostgreSQL. Frontend is React plus
TypeScript plus Vite plus TanStack Query. Realtime is polling. The full specification lives
in `INSTRUCTIONS.md` and `PROJECT.md` at the repository root; that specification is the
contract and wins any conflict about product behavior or API shape.

## Code quality rules (always apply)

These are non-negotiable in every file and every language.

- No comments, docstrings, or JSDoc. The only exception is the `Why this change is needed`
  block at the top of an Alembic migration.
- No emojis. No em-dash or en-dash characters. Use a plain hyphen, comma, or parentheses.
  Use the ASCII `->` only when a literal arrow is required.
- English-only identifiers. No filler prepositions (`function_value`, not
  `function_with_value`). No fluff prefixes or suffixes (`Enhanced`, `New`, `V2`, `Temp`,
  `Manager`, `Helper`, `Utils`) without real domain meaning.
- Booleans use `is_`, `has_`, `can_`, `should_`. Counters end in `_count` or `_total`.
- Acronyms stay uppercase in PascalCase and SCREAMING_SNAKE_CASE (`HTTPClient`, `UUID`,
  `API_BASE_URL`) and lowercase in snake_case (`http_client`, `api_base_url`).
- No magic numbers or hardcoded URLs, paths, timeouts, or limits. Runtime configuration
  lives in `backend/app/core/config.py` (Pydantic `BaseSettings`). Frontend polling
  intervals and the API base URL live in `frontend/src/config.ts`.
- Enumerations use `Enum` (Python) or string-literal unions (TypeScript), never loose
  string constants.
- No placeholder markers (`TODO`, `FIXME`, `HACK`, `XXX`) in committed code.
- No dead code, no unused imports, no commented-out code.
- No `print`, `console.log`, `debugger`, or stray debug logging in committed code. Scripts
  (seed, simulator) log through a configured logger, which is intentional output.
- No `any` in TypeScript. No untyped parameters in Python. Every function has an explicit
  return type. Every nullable value is handled explicitly.
- All imports at module top. No imports inside functions or methods except a
  `TYPE_CHECKING` block to break a genuine import cycle.
- External input is validated with Pydantic (backend) or typed parsing (frontend).
- SQL is parameterized through SQLAlchemy. No string concatenation into queries.
- No secrets in code or Compose. Use `${VAR}` passthrough and `.env` (git-ignored).
  Only `.env.example` is committed.
- Commits follow Conventional Commits. One logical change per commit.

## Architecture rules

- Layered backend: `domain` (enums, zones, pure rules), `schemas` (Pydantic DTOs),
  `repositories` (database access), `services` (use-case logic and transaction boundaries),
  `api/routes` (thin handlers that validate, call a service, return a response).
- Route handlers stay thin. Transaction-sensitive logic lives in services, never in routes.
- Repositories never own transactions. Services own transaction boundaries
  (`async with session.begin()`), so a use case commits exactly once.
- Business logic never lives inside SQLAlchemy models.
- Database sessions are provided by dependency injection, one session per request.
- UUID7 (via `uuid_utils`) for all generated UUID primary keys. Never UUID4.
- Timezone-aware datetimes, stored in UTC.
- Structured logging via `structlog`.

## Deliberate deviations from the stricter house style

This repository is an external assessment, not a Becton platform service. The following
platform mandates are intentionally not applied here, because the assessment specification
either defines a different contract or explicitly scopes the concern out. Each deviation is
a reasoned decision, recorded so reviewers understand it was a choice, not an oversight.

- No Zeus Auth or any authentication. The specification states authentication is out of
  scope. CORS is still configured explicitly to the frontend origin (no wildcard).
- Response bodies for single resources and bounded collections follow the exact shapes
  defined in `INSTRUCTIONS.md` (for example `{ "vehicles": [...] }`), not a generic
  `ApiResponse[T]` envelope. The spec is the API contract the frontend consumes.
- Pagination is applied only where a collection grows without bound. `GET /anomalies` uses
  keyset (cursor) pagination with a generic `PaginatedResponse[T]` envelope (`items`,
  `next_cursor`, `has_more`). The bounded collections (50 vehicles, 20 zones) are returned
  whole, because paginating fixed-size sets adds machinery without value.
- The frontend uses MUI (Material UI). Styling goes through the MUI theme and the `sx`
  prop (the theme-token styling API compiled to classes by emotion), not raw ad-hoc
  `style={{...}}` attributes.
- No OpenTelemetry and no Prometheus in v1. The specification lists an observability stack
  as a future improvement and asks not to overengineer. This is documented in the ADR.
- No native PostgreSQL enum types. Status-like columns are stored as strings and validated
  by Python `Enum` plus Pydantic. This keeps migrations simple while staying type-safe at
  the application boundary. The specification explicitly allows enum or string.

## Concurrency rules (the heart of this project)

- Zone counters are incremented with a single database statement
  (`INSERT ... ON CONFLICT (zone_id) DO UPDATE SET entry_count = entry_count + 1`). Never
  select-then-add-then-update in Python.
- The fault transition locks the vehicle row with `SELECT ... FOR UPDATE` before touching
  the mission or maintenance record, and relies on partial unique indexes
  (`unique(vehicle_id) where status = 'active'` and `... where status = 'open'`) as a
  database-level backstop against duplicates.
- Telemetry ingestion is one transaction: it commits once at the end, or rolls back
  entirely. Telemetry arriving with `status == "fault"` calls the same fault transition
  service used by the status endpoint. The logic is not duplicated.
- Every concurrency guarantee has a test that exercises it with real concurrent requests
  against PostgreSQL.

## Working agreement

- Read `INSTRUCTIONS.md` and `PROJECT.md` before changing behavior.
- Run validation after changes: `ruff` for lint, `pytest` for the backend, `tsc` plus
  `vite build` for the frontend.
- Never claim tests pass without running them. If a test cannot run, document why in the
  README under Known limitations.
- Keep the README, ADR, and AI interaction log truthful and current.
