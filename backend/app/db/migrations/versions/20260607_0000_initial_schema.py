# Why this change is needed:
# Creates the full Telemetry Hub schema in one initial migration: vehicles, telemetry
# events, zone counters, anomalies, missions and maintenance records. Includes the partial
# unique indexes that guarantee one active mission and one open maintenance record per
# vehicle, the telemetry validation check constraints, and seeds the 20 fixed zone rows.
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.domain.zones import ZONES

revision: str = "20260607_0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", sa.String(50), primary_key=True),
        sa.Column("current_status", sa.String(20), nullable=False),
        sa.Column("battery_pct", sa.Integer(), nullable=True),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vehicles_current_status", "vehicles", ["current_status"])
    op.create_index("ix_vehicles_last_seen_at", "vehicles", ["last_seen_at"])

    op.create_table(
        "zone_counters",
        sa.Column("zone_id", sa.String(50), primary_key=True),
        sa.Column("entry_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", sa.String(50), sa.ForeignKey("vehicles.vehicle_id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_missions_vehicle_id", "missions", ["vehicle_id"])
    op.create_index(
        "uq_active_mission_per_vehicle",
        "missions",
        ["vehicle_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "telemetry_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", sa.String(50), sa.ForeignKey("vehicles.vehicle_id"), nullable=False),
        sa.Column("vehicle_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("battery_pct", sa.Integer(), nullable=False),
        sa.Column("speed_mps", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "error_codes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("zone_entered", sa.String(50), nullable=True),
        sa.CheckConstraint("battery_pct >= 0 AND battery_pct <= 100", name="ck_telemetry_battery_range"),
        sa.CheckConstraint("speed_mps >= 0", name="ck_telemetry_speed_nonneg"),
        sa.CheckConstraint("lat >= -90 AND lat <= 90", name="ck_telemetry_lat_range"),
        sa.CheckConstraint("lon >= -180 AND lon <= 180", name="ck_telemetry_lon_range"),
    )
    op.create_index("ix_telemetry_vehicle_timestamp", "telemetry_events", ["vehicle_id", "vehicle_timestamp"])
    op.create_index("ix_telemetry_received_at", "telemetry_events", ["received_at"])
    op.create_index("ix_telemetry_status", "telemetry_events", ["status"])
    op.create_index("ix_telemetry_zone_entered", "telemetry_events", ["zone_entered"])

    op.create_table(
        "anomalies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", sa.String(50), sa.ForeignKey("vehicles.vehicle_id"), nullable=False),
        sa.Column(
            "telemetry_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("telemetry_events.id"),
            nullable=True,
        ),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index(
        "ix_anomalies_vehicle_observed",
        "anomalies",
        ["vehicle_id", sa.text("observed_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "ix_anomalies_observed_at",
        "anomalies",
        [sa.text("observed_at DESC"), sa.text("id DESC")],
    )
    op.create_index("ix_anomalies_type", "anomalies", ["type"])
    op.create_index("ix_anomalies_severity", "anomalies", ["severity"])

    op.create_table(
        "maintenance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", sa.String(50), sa.ForeignKey("vehicles.vehicle_id"), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_maintenance_vehicle_id", "maintenance_records", ["vehicle_id"])
    op.create_index(
        "uq_open_maintenance_per_vehicle",
        "maintenance_records",
        ["vehicle_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )

    zone_counters_table = sa.table("zone_counters", sa.column("zone_id", sa.String))
    op.bulk_insert(zone_counters_table, [{"zone_id": zone_id} for zone_id in ZONES])


def downgrade() -> None:
    op.drop_table("maintenance_records")
    op.drop_table("anomalies")
    op.drop_table("telemetry_events")
    op.drop_table("missions")
    op.drop_table("zone_counters")
    op.drop_table("vehicles")
