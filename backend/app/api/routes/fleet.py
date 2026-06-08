from fastapi import APIRouter, Depends

from app.api.deps import get_fleet_state_service
from app.schemas.fleet import FleetStateResponse
from app.services.fleet_state_service import FleetStateService

router = APIRouter(tags=["fleet"])


@router.get("/fleet/state", response_model=FleetStateResponse)
async def fleet_state(
    service: FleetStateService = Depends(get_fleet_state_service),
) -> FleetStateResponse:
    return await service.get_state()
