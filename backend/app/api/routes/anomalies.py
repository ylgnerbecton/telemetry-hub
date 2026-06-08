from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_anomaly_service
from app.core.pagination import InvalidCursorError
from app.schemas.anomalies import AnomalyRead
from app.schemas.pagination import PaginatedResponse
from app.services.anomaly_service import AnomalyService

router = APIRouter(tags=["anomalies"])


@router.get("/anomalies", response_model=PaginatedResponse[AnomalyRead])
async def list_anomalies(
    vehicle_id: str | None = Query(default=None),
    time_from: datetime | None = Query(default=None, alias="from"),
    time_to: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=500),
    cursor: str | None = Query(default=None),
    service: AnomalyService = Depends(get_anomaly_service),
) -> PaginatedResponse[AnomalyRead]:
    try:
        return await service.query(
            vehicle_id=vehicle_id,
            time_from=time_from,
            time_to=time_to,
            cursor=cursor,
            limit=limit,
        )
    except InvalidCursorError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
