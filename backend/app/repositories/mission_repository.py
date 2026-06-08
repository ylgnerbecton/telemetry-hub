from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mission
from app.domain.enums import MissionStatus


class MissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_for_update(self, vehicle_id: str) -> Mission | None:
        result = await self._session.execute(
            select(Mission)
            .where(
                Mission.vehicle_id == vehicle_id,
                Mission.status == MissionStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def cancel(self, mission: Mission, *, cancelled_at: datetime, reason: str) -> None:
        mission.status = MissionStatus.CANCELLED.value
        mission.cancelled_at = cancelled_at
        mission.cancellation_reason = reason
