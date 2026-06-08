from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://telemetry:telemetry@localhost:5432/telemetry_hub"
    test_database_url: str = "postgresql+asyncpg://telemetry:telemetry@localhost:5432/telemetry_hub_test"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "info"
    simulator_target_url: str = "http://localhost:8000"

    db_pool_size: int = 20
    db_max_overflow: int = 40

    low_battery_threshold_pct: int = 15
    overspeed_threshold_mps: float = 5.0
    stale_telemetry_max_age_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
