from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_vehicle_read_service, get_vehicle_status_service
from app.schemas.vehicles import (
    VehiclesResponse,
    VehicleStatusUpdate,
    VehicleStatusUpdateResponse,
)
from app.services.vehicle_read_service import VehicleReadService
from app.services.vehicle_status_service import (
    VehicleNotFoundError,
    VehicleStatusService,
)

router = APIRouter(tags=["vehicles"])


@router.get("/vehicles", response_model=VehiclesResponse)
async def list_vehicles(
    service: VehicleReadService = Depends(get_vehicle_read_service),
) -> VehiclesResponse:
    return await service.list_vehicles()


@router.patch("/vehicles/{vehicle_id}/status", response_model=VehicleStatusUpdateResponse)
async def update_vehicle_status(
    vehicle_id: str,
    payload: VehicleStatusUpdate,
    service: VehicleStatusService = Depends(get_vehicle_status_service),
) -> VehicleStatusUpdateResponse:
    try:
        return await service.update_status(vehicle_id, payload.status)
    except VehicleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
