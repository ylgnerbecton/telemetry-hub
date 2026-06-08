from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ZoneCounter


class ZoneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def increment(self, zone_id: str, *, updated_at: datetime) -> None:
        stmt = insert(ZoneCounter).values(zone_id=zone_id, entry_count=1, updated_at=updated_at)
        stmt = stmt.on_conflict_do_update(
            index_elements=["zone_id"],
            set_={
                "entry_count": ZoneCounter.entry_count + 1,
                "updated_at": updated_at,
            },
        )
        await self._session.execute(stmt)

    async def list_counts(self) -> list[ZoneCounter]:
        result = await self._session.execute(select(ZoneCounter).order_by(ZoneCounter.zone_id))
        return list(result.scalars().all())
