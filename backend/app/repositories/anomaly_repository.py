from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import CursorPosition
from app.db.models import Anomaly


class AnomalyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add_many(self, anomalies: list[Anomaly]) -> None:
        self._session.add_all(anomalies)

    async def query(
        self,
        *,
        vehicle_id: str | None,
        time_from: datetime | None,
        time_to: datetime | None,
        cursor: CursorPosition | None,
        limit: int,
    ) -> list[Anomaly]:
        stmt = select(Anomaly)
        if vehicle_id is not None:
            stmt = stmt.where(Anomaly.vehicle_id == vehicle_id)
        if time_from is not None:
            stmt = stmt.where(Anomaly.observed_at >= time_from)
        if time_to is not None:
            stmt = stmt.where(Anomaly.observed_at <= time_to)
        if cursor is not None:
            stmt = stmt.where(tuple_(Anomaly.observed_at, Anomaly.id) < tuple_(cursor.observed_at, cursor.anomaly_id))
        stmt = stmt.order_by(Anomaly.observed_at.desc(), Anomaly.id.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def most_recent_by_vehicle(self) -> dict[str, Anomaly]:
        stmt = select(Anomaly).distinct(Anomaly.vehicle_id).order_by(Anomaly.vehicle_id, Anomaly.observed_at.desc())
        result = await self._session.execute(stmt)
        return {anomaly.vehicle_id: anomaly for anomaly in result.scalars().all()}
