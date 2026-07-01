from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WeatherQuery(BaseModel):
    farm_id: int | None = Field(default=None, gt=0)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)

    @model_validator(mode="after")
    def validate_location(self) -> "WeatherQuery":
        has_farm = self.farm_id is not None
        has_coordinates = self.longitude is not None and self.latitude is not None
        if not has_farm and not has_coordinates:
            raise ValueError("farm_id or longitude and latitude are required")
        if has_farm and has_coordinates:
            raise ValueError("Use farm_id or coordinates, not both")
        if (self.longitude is None) != (self.latitude is None):
            raise ValueError("longitude and latitude must be provided together")
        return self


class WeatherLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int | None = None
    name: str | None = None
    latitude: Decimal
    longitude: Decimal
    source: str


class WeatherMetricRead(BaseModel):
    temperature_c: Decimal | None = None
    humidity_percent: Decimal | None = None
    rainfall_mm: Decimal | None = None
    wind_speed_kmh: Decimal | None = None
    pressure_hpa: Decimal | None = None
    cloud_cover_percent: Decimal | None = None


class CurrentWeatherRead(WeatherMetricRead):
    provider: str
    location: WeatherLocationRead
    observed_at: datetime
    fetched_at: datetime


class HourlyForecastRead(WeatherMetricRead):
    provider: str
    location: WeatherLocationRead
    forecast_time: datetime
    fetched_at: datetime


class DailyForecastRead(BaseModel):
    provider: str
    location: WeatherLocationRead
    forecast_date: date
    temperature_min_c: Decimal | None = None
    temperature_max_c: Decimal | None = None
    humidity_percent: Decimal | None = None
    rainfall_mm: Decimal | None = None
    wind_speed_kmh: Decimal | None = None
    pressure_hpa: Decimal | None = None
    cloud_cover_percent: Decimal | None = None
    fetched_at: datetime


class WeatherObservationRead(WeatherMetricRead):
    provider: str
    location: WeatherLocationRead
    observed_at: datetime
    fetched_at: datetime


class CurrentWeatherResponse(BaseModel):
    current: CurrentWeatherRead


class HourlyForecastResponse(BaseModel):
    hourly: list[HourlyForecastRead]


class DailyForecastResponse(BaseModel):
    daily: list[DailyForecastRead]


class WeatherHistoryResponse(BaseModel):
    observations: list[WeatherObservationRead]
