from fastapi import APIRouter, Depends, status

from app.api.deps import get_telemetry_service
from app.schemas.telemetry import TelemetryIngest, TelemetryIngestResponse
from app.services.telemetry_service import TelemetryService

router = APIRouter(tags=["telemetry"])


@router.post(
    "/telemetry",
    response_model=TelemetryIngestResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry(
    payload: TelemetryIngest,
    service: TelemetryService = Depends(get_telemetry_service),
) -> TelemetryIngestResponse:
    return await service.ingest(payload)
