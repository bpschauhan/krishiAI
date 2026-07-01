from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WeatherLocation(Base):
    __tablename__ = "weather_locations"
    __table_args__ = (UniqueConstraint("farm_id", name="uq_weather_locations_farm_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int | None] = mapped_column(ForeignKey("farms.id"), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="farm_boundary")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    farm = relationship("Farm")


class CurrentWeather(Base):
    __tablename__ = "current_weather"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("weather_locations.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    location = relationship("WeatherLocation")


class HourlyForecast(Base):
    __tablename__ = "hourly_forecasts"
    __table_args__ = (UniqueConstraint("location_id", "provider", "forecast_time", name="uq_hourly_forecasts_location_provider_time"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("weather_locations.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    location = relationship("WeatherLocation")


class DailyForecast(Base):
    __tablename__ = "daily_forecasts"
    __table_args__ = (UniqueConstraint("location_id", "provider", "forecast_date", name="uq_daily_forecasts_location_provider_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("weather_locations.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    temperature_min_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    temperature_max_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    location = relationship("WeatherLocation")


class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    __table_args__ = (UniqueConstraint("location_id", "provider", "observed_at", name="uq_weather_observations_location_provider_time"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("weather_locations.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    humidity_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rainfall_mm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    wind_speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    pressure_hpa: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    location = relationship("WeatherLocation")
