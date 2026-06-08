from fastapi import APIRouter, Depends

from app.api.deps import get_zone_counter_service
from app.schemas.zones import ZonesResponse
from app.services.zone_counter_service import ZoneCounterService

router = APIRouter(tags=["zones"])


@router.get("/zones/counts", response_model=ZonesResponse)
async def zone_counts(
    service: ZoneCounterService = Depends(get_zone_counter_service),
) -> ZonesResponse:
    return await service.list_counts()
