from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.zone_repository import ZoneRepository
from app.schemas.zones import ZoneCountRead, ZonesResponse


class ZoneCounterService:
    def __init__(self, session: AsyncSession) -> None:
        self._zones = ZoneRepository(session)

    async def list_counts(self) -> ZonesResponse:
        rows = await self._zones.list_counts()
        return ZonesResponse(zones=[ZoneCountRead.model_validate(row) for row in rows])
