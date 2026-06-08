import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MaintenanceRecord
from app.domain.enums import MaintenanceStatus


class MaintenanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_open_for_update(self, vehicle_id: str) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.vehicle_id == vehicle_id,
                MaintenanceRecord.status == MaintenanceStatus.OPEN.value,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        vehicle_id: str,
        mission_id: uuid.UUID | None,
        reason: str,
        created_at: datetime,
    ) -> MaintenanceRecord:
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            mission_id=mission_id,
            status=MaintenanceStatus.OPEN.value,
            reason=reason,
            created_at=created_at,
        )
        self._session.add(record)
        return record
