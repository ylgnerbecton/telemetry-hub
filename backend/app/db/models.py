import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import generate_uuid7
from app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    current_status: Mapped[str] = mapped_column(String(20), nullable=False)
    battery_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_vehicles_current_status", "current_status"),
        Index("ix_vehicles_last_seen_at", "last_seen_at"),
    )


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    vehicle_id: Mapped[str] = mapped_column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False)
    vehicle_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    battery_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_codes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    zone_entered: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_telemetry_vehicle_timestamp", "vehicle_id", "vehicle_timestamp"),
        Index("ix_telemetry_received_at", "received_at"),
        Index("ix_telemetry_status", "status"),
        Index("ix_telemetry_zone_entered", "zone_entered"),
        CheckConstraint("battery_pct >= 0 AND battery_pct <= 100", name="ck_telemetry_battery_range"),
        CheckConstraint("speed_mps >= 0", name="ck_telemetry_speed_nonneg"),
        CheckConstraint("lat >= -90 AND lat <= 90", name="ck_telemetry_lat_range"),
        CheckConstraint("lon >= -180 AND lon <= 180", name="ck_telemetry_lon_range"),
    )


class ZoneCounter(Base):
    __tablename__ = "zone_counters"

    zone_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entry_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    vehicle_id: Mapped[str] = mapped_column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False)
    telemetry_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("telemetry_events.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    context: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (
        Index("ix_anomalies_type", "type"),
        Index("ix_anomalies_severity", "severity"),
    )


Index(
    "ix_anomalies_vehicle_observed",
    Anomaly.vehicle_id,
    Anomaly.observed_at.desc(),
    Anomaly.id.desc(),
)
Index("ix_anomalies_observed_at", Anomaly.observed_at.desc(), Anomaly.id.desc())


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    vehicle_id: Mapped[str] = mapped_column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_missions_vehicle_id", "vehicle_id"),
        Index(
            "uq_active_mission_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    vehicle_id: Mapped[str] = mapped_column(String(50), ForeignKey("vehicles.vehicle_id"), nullable=False)
    mission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_maintenance_vehicle_id", "vehicle_id"),
        Index(
            "uq_open_maintenance_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )
