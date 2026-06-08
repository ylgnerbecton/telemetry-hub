.DEFAULT_GOAL := help
.PHONY: help up down logs backend-install backend-dev backend-test migrate seed simulate frontend-install frontend-dev frontend-build lint fmt

help:
	@echo "Telemetry Hub - available commands:"
	@echo "  make up                 Start postgres, backend and frontend via Docker Compose"
	@echo "  make down               Stop all Docker Compose services"
	@echo "  make logs               Tail Docker Compose logs"
	@echo "  make backend-install    Create backend venv and install dependencies"
	@echo "  make backend-dev        Run the backend with autoreload"
	@echo "  make backend-test       Run the backend test suite (needs postgres running)"
	@echo "  make migrate            Apply Alembic migrations"
	@echo "  make seed               Seed 50 vehicles, missions and 20 zones"
	@echo "  make simulate           Stream simulated telemetry to the backend"
	@echo "  make frontend-install   Install frontend dependencies"
	@echo "  make frontend-dev       Run the frontend dev server"
	@echo "  make frontend-build     Type-check and build the frontend"
	@echo "  make lint               Lint backend (ruff) and frontend (tsc)"
	@echo "  make fmt                Format backend code with ruff"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-install:
	cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]"

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && .venv/bin/pytest

migrate:
	cd backend && .venv/bin/alembic upgrade head

seed:
	cd backend && .venv/bin/python scripts/seed.py

simulate:
	cd backend && .venv/bin/python scripts/simulate_telemetry.py

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

lint:
	cd backend && .venv/bin/ruff check .
	cd frontend && npm run lint

fmt:
	cd backend && .venv/bin/ruff format .
