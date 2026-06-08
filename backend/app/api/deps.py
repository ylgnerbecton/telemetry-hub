from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.anomaly_service import AnomalyService
from app.services.fleet_state_service import FleetStateService
from app.services.telemetry_service import TelemetryService
from app.services.vehicle_read_service import VehicleReadService
from app.services.vehicle_status_service import VehicleStatusService
from app.services.zone_counter_service import ZoneCounterService


def get_telemetry_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TelemetryService:
    return TelemetryService(session, settings)


def get_anomaly_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AnomalyService:
    return AnomalyService(session, settings)


def get_vehicle_read_service(session: AsyncSession = Depends(get_db)) -> VehicleReadService:
    return VehicleReadService(session)


def get_vehicle_status_service(session: AsyncSession = Depends(get_db)) -> VehicleStatusService:
    return VehicleStatusService(session)


def get_fleet_state_service(session: AsyncSession = Depends(get_db)) -> FleetStateService:
    return FleetStateService(session)


def get_zone_counter_service(session: AsyncSession = Depends(get_db)) -> ZoneCounterService:
    return ZoneCounterService(session)
