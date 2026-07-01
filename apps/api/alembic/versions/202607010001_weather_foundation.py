"""create weather foundation tables

Revision ID: 202607010001
Revises: 202606300002
Create Date: 2026-07-01 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607010001"
down_revision: str | None = "202606300002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weather_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farm_id", name="uq_weather_locations_farm_id"),
    )
    op.create_index(op.f("ix_weather_locations_id"), "weather_locations", ["id"], unique=False)
    op.create_index(op.f("ix_weather_locations_farm_id"), "weather_locations", ["farm_id"], unique=False)

    op.create_table(
        "current_weather",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("wind_speed_kmh", sa.Numeric(8, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(8, 2), nullable=True),
        sa.Column("cloud_cover_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["weather_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_current_weather_id"), "current_weather", ["id"], unique=False)
    op.create_index(op.f("ix_current_weather_location_id"), "current_weather", ["location_id"], unique=False)
    op.create_index(op.f("ix_current_weather_observed_at"), "current_weather", ["observed_at"], unique=False)

    op.create_table(
        "hourly_forecasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("forecast_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("wind_speed_kmh", sa.Numeric(8, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(8, 2), nullable=True),
        sa.Column("cloud_cover_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["weather_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "provider", "forecast_time", name="uq_hourly_forecasts_location_provider_time"),
    )
    op.create_index(op.f("ix_hourly_forecasts_id"), "hourly_forecasts", ["id"], unique=False)
    op.create_index(op.f("ix_hourly_forecasts_location_id"), "hourly_forecasts", ["location_id"], unique=False)
    op.create_index(op.f("ix_hourly_forecasts_forecast_time"), "hourly_forecasts", ["forecast_time"], unique=False)

    op.create_table(
        "daily_forecasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("temperature_min_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("temperature_max_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("wind_speed_kmh", sa.Numeric(8, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(8, 2), nullable=True),
        sa.Column("cloud_cover_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["weather_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "provider", "forecast_date", name="uq_daily_forecasts_location_provider_date"),
    )
    op.create_index(op.f("ix_daily_forecasts_id"), "daily_forecasts", ["id"], unique=False)
    op.create_index(op.f("ix_daily_forecasts_location_id"), "daily_forecasts", ["location_id"], unique=False)
    op.create_index(op.f("ix_daily_forecasts_forecast_date"), "daily_forecasts", ["forecast_date"], unique=False)

    op.create_table(
        "weather_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("humidity_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=True),
        sa.Column("wind_speed_kmh", sa.Numeric(8, 2), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(8, 2), nullable=True),
        sa.Column("cloud_cover_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["weather_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id", "provider", "observed_at", name="uq_weather_observations_location_provider_time"),
    )
    op.create_index(op.f("ix_weather_observations_id"), "weather_observations", ["id"], unique=False)
    op.create_index(op.f("ix_weather_observations_location_id"), "weather_observations", ["location_id"], unique=False)
    op.create_index(op.f("ix_weather_observations_observed_at"), "weather_observations", ["observed_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_weather_observations_observed_at"), table_name="weather_observations")
    op.drop_index(op.f("ix_weather_observations_location_id"), table_name="weather_observations")
    op.drop_index(op.f("ix_weather_observations_id"), table_name="weather_observations")
    op.drop_table("weather_observations")

    op.drop_index(op.f("ix_daily_forecasts_forecast_date"), table_name="daily_forecasts")
    op.drop_index(op.f("ix_daily_forecasts_location_id"), table_name="daily_forecasts")
    op.drop_index(op.f("ix_daily_forecasts_id"), table_name="daily_forecasts")
    op.drop_table("daily_forecasts")

    op.drop_index(op.f("ix_hourly_forecasts_forecast_time"), table_name="hourly_forecasts")
    op.drop_index(op.f("ix_hourly_forecasts_location_id"), table_name="hourly_forecasts")
    op.drop_index(op.f("ix_hourly_forecasts_id"), table_name="hourly_forecasts")
    op.drop_table("hourly_forecasts")

    op.drop_index(op.f("ix_current_weather_observed_at"), table_name="current_weather")
    op.drop_index(op.f("ix_current_weather_location_id"), table_name="current_weather")
    op.drop_index(op.f("ix_current_weather_id"), table_name="current_weather")
    op.drop_table("current_weather")

    op.drop_index(op.f("ix_weather_locations_farm_id"), table_name="weather_locations")
    op.drop_index(op.f("ix_weather_locations_id"), table_name="weather_locations")
    op.drop_table("weather_locations")
