import asyncio
from collections.abc import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import get_db
from app.domain.zones import ZONES
from app.main import app

settings = get_settings()
TEST_URL = settings.test_database_url
_TABLES = "anomalies, maintenance_records, missions, telemetry_events, zone_counters, vehicles"


async def _ensure_database() -> None:
    url = make_url(TEST_URL)
    admin = await asyncpg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        database="postgres",
    )
    try:
        exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database)
        if not exists:
            await admin.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await admin.close()


async def _create_schema() -> None:
    engine = create_async_engine(TEST_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
    asyncio.run(_ensure_database())
    asyncio.run(_create_schema())


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    instance = create_async_engine(TEST_URL, pool_size=20, max_overflow=60, pool_pre_ping=True)
    yield instance
    await instance.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {_TABLES} RESTART IDENTITY CASCADE"))
        await conn.execute(
            text("INSERT INTO zone_counters (zone_id) VALUES (:zone_id)"),
            [{"zone_id": zone_id} for zone_id in ZONES],
        )


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as instance:
        yield instance


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with factory() as instance:
            yield instance

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as instance:
        yield instance
    app.dependency_overrides.clear()
