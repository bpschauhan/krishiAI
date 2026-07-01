from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.farm import Farm
from app.models.geospatial import FarmBoundary
from app.models.weather import CurrentWeather, DailyForecast, HourlyForecast, WeatherLocation, WeatherObservation
from app.schemas.weather import (
    CurrentWeatherRead,
    CurrentWeatherResponse,
    DailyForecastRead,
    DailyForecastResponse,
    HourlyForecastRead,
    HourlyForecastResponse,
    WeatherHistoryResponse,
    WeatherLocationRead,
    WeatherObservationRead,
    WeatherQuery,
)
from app.services.spatial_intelligence import polygon_centroid
from app.services.weather_cache import WeatherCache, weather_cache
from app.services.weather_provider import (
    CurrentWeatherData,
    DailyForecastData,
    HourlyForecastData,
    OpenMeteoProvider,
    WeatherObservationData,
    WeatherProvider,
)


class WeatherService:
    def __init__(
        self,
        provider: WeatherProvider | None = None,
        cache: WeatherCache | None = None,
    ) -> None:
        self.provider = provider or OpenMeteoProvider()
        self.cache = cache or weather_cache

    def current_weather(self, session: Session, query: WeatherQuery) -> CurrentWeatherResponse:
        location = self._resolve_location(session, query)
        cache_key = self._cache_key("current", location)
        cached = self.cache.get_json(cache_key)
        if cached:
            return CurrentWeatherResponse.model_validate(cached)

        data = self.provider.current_weather(float(location.latitude), float(location.longitude))
        record = self._store_current_weather(session, location, data)
        response = CurrentWeatherResponse(current=self._current_read(location, record))
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def hourly_forecast(self, session: Session, query: WeatherQuery, hours: int = 24) -> HourlyForecastResponse:
        location = self._resolve_location(session, query)
        cache_key = self._cache_key("hourly", location, extra=str(hours))
        cached = self.cache.get_json(cache_key)
        if cached:
            return HourlyForecastResponse.model_validate(cached)

        data = self.provider.hourly_forecast(float(location.latitude), float(location.longitude), hours=hours)
        records = self._store_hourly_forecasts(session, location, data)
        response = HourlyForecastResponse(hourly=[self._hourly_read(location, record) for record in records])
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def daily_forecast(self, session: Session, query: WeatherQuery, days: int = 7) -> DailyForecastResponse:
        location = self._resolve_location(session, query)
        cache_key = self._cache_key("daily", location, extra=str(days))
        cached = self.cache.get_json(cache_key)
        if cached:
            return DailyForecastResponse.model_validate(cached)

        data = self.provider.daily_forecast(float(location.latitude), float(location.longitude), days=days)
        records = self._store_daily_forecasts(session, location, data)
        response = DailyForecastResponse(daily=[self._daily_read(location, record) for record in records])
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def historical_weather(
        self,
        session: Session,
        query: WeatherQuery,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> WeatherHistoryResponse:
        location = self._resolve_location(session, query)
        resolved_end = end_date or date.today() - timedelta(days=1)
        resolved_start = start_date or resolved_end
        if resolved_start > resolved_end:
            raise ValueError("start_date must be before or equal to end_date")

        cache_key = self._cache_key("history", location, extra=f"{resolved_start}:{resolved_end}")
        cached = self.cache.get_json(cache_key)
        if cached:
            return WeatherHistoryResponse.model_validate(cached)

        data = self.provider.historical_weather(
            float(location.latitude),
            float(location.longitude),
            start_date=resolved_start,
            end_date=resolved_end,
        )
        records = self._store_observations(session, location, data)
        response = WeatherHistoryResponse(observations=[self._observation_read(location, record) for record in records])
        self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response

    def sync_farm_weather(self, session: Session, farm_id: int) -> CurrentWeatherResponse:
        return self.current_weather(session, WeatherQuery(farm_id=farm_id))

    def sync_farm_forecasts(self, session: Session, farm_id: int) -> tuple[HourlyForecastResponse, DailyForecastResponse]:
        query = WeatherQuery(farm_id=farm_id)
        return self.hourly_forecast(session, query), self.daily_forecast(session, query)

    def _resolve_location(self, session: Session, query: WeatherQuery) -> WeatherLocation:
        if query.farm_id is not None:
            farm = session.get(Farm, query.farm_id)
            if farm is None:
                raise LookupError("Farm not found")
            centroid = self._farm_centroid(session, query.farm_id)
            location = session.scalar(select(WeatherLocation).where(WeatherLocation.farm_id == query.farm_id))
            if location is None:
                location = WeatherLocation(
                    farm_id=query.farm_id,
                    name=farm.name,
                    latitude=Decimal(str(round(centroid.latitude, 6))),
                    longitude=Decimal(str(round(centroid.longitude, 6))),
                    source="farm_boundary",
                )
                session.add(location)
            else:
                location.name = farm.name
                location.latitude = Decimal(str(round(centroid.latitude, 6)))
                location.longitude = Decimal(str(round(centroid.longitude, 6)))
            session.flush()
            return location

        if query.latitude is None or query.longitude is None:
            raise LookupError("Weather location not found")
        location = WeatherLocation(
            farm_id=None,
            name="Coordinate lookup",
            latitude=Decimal(str(round(query.latitude, 6))),
            longitude=Decimal(str(round(query.longitude, 6))),
            source="coordinates",
        )
        session.add(location)
        session.flush()
        return location

    def _farm_centroid(self, session: Session, farm_id: int):
        if session.get_bind().dialect.name == "postgresql":
            row = session.execute(
                text(
                    """
                    select ST_AsGeoJSON(geometry) as geometry
                    from farm_boundaries
                    where farm_id = :farm_id
                    order by id
                    limit 1
                    """
                ),
                {"farm_id": farm_id},
            ).mappings().first()
            if row is None:
                raise LookupError("Farm boundary not found")
            return polygon_centroid(json.loads(row["geometry"]))

        boundary = session.scalar(select(FarmBoundary).where(FarmBoundary.farm_id == farm_id).order_by(FarmBoundary.id))
        if boundary is None:
            raise LookupError("Farm boundary not found")
        return polygon_centroid(boundary.geometry)

    def _store_current_weather(
        self,
        session: Session,
        location: WeatherLocation,
        data: CurrentWeatherData,
    ) -> CurrentWeather:
        record = CurrentWeather(
            location_id=location.id,
            provider=self.provider.name,
            observed_at=data.observed_at,
            fetched_at=_now(),
            temperature_c=data.temperature_c,
            humidity_percent=data.humidity_percent,
            rainfall_mm=data.rainfall_mm,
            wind_speed_kmh=data.wind_speed_kmh,
            pressure_hpa=data.pressure_hpa,
            cloud_cover_percent=data.cloud_cover_percent,
        )
        session.add(record)
        session.commit()
        session.refresh(location)
        session.refresh(record)
        return record

    def _store_hourly_forecasts(
        self,
        session: Session,
        location: WeatherLocation,
        data: list[HourlyForecastData],
    ) -> list[HourlyForecast]:
        records = []
        fetched_at = _now()
        for item in data:
            record = session.scalar(
                select(HourlyForecast).where(
                    HourlyForecast.location_id == location.id,
                    HourlyForecast.provider == self.provider.name,
                    HourlyForecast.forecast_time == item.forecast_time,
                )
            )
            if record is None:
                record = HourlyForecast(location_id=location.id, provider=self.provider.name, forecast_time=item.forecast_time)
                session.add(record)
            _assign_metric_fields(record, item)
            record.fetched_at = fetched_at
            records.append(record)
        session.commit()
        session.refresh(location)
        for record in records:
            session.refresh(record)
        return records

    def _store_daily_forecasts(
        self,
        session: Session,
        location: WeatherLocation,
        data: list[DailyForecastData],
    ) -> list[DailyForecast]:
        records = []
        fetched_at = _now()
        for item in data:
            record = session.scalar(
                select(DailyForecast).where(
                    DailyForecast.location_id == location.id,
                    DailyForecast.provider == self.provider.name,
                    DailyForecast.forecast_date == item.forecast_date,
                )
            )
            if record is None:
                record = DailyForecast(location_id=location.id, provider=self.provider.name, forecast_date=item.forecast_date)
                session.add(record)
            record.temperature_min_c = item.temperature_min_c
            record.temperature_max_c = item.temperature_max_c
            record.humidity_percent = item.humidity_percent
            record.rainfall_mm = item.rainfall_mm
            record.wind_speed_kmh = item.wind_speed_kmh
            record.pressure_hpa = item.pressure_hpa
            record.cloud_cover_percent = item.cloud_cover_percent
            record.fetched_at = fetched_at
            records.append(record)
        session.commit()
        session.refresh(location)
        for record in records:
            session.refresh(record)
        return records

    def _store_observations(
        self,
        session: Session,
        location: WeatherLocation,
        data: list[WeatherObservationData],
    ) -> list[WeatherObservation]:
        records = []
        fetched_at = _now()
        for item in data:
            record = session.scalar(
                select(WeatherObservation).where(
                    WeatherObservation.location_id == location.id,
                    WeatherObservation.provider == self.provider.name,
                    WeatherObservation.observed_at == item.observed_at,
                )
            )
            if record is None:
                record = WeatherObservation(location_id=location.id, provider=self.provider.name, observed_at=item.observed_at)
                session.add(record)
            _assign_metric_fields(record, item)
            record.fetched_at = fetched_at
            records.append(record)
        session.commit()
        session.refresh(location)
        for record in records:
            session.refresh(record)
        return records

    def _location_read(self, location: WeatherLocation) -> WeatherLocationRead:
        return WeatherLocationRead(
            id=location.id,
            farm_id=location.farm_id,
            name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            source=location.source,
        )

    def _current_read(self, location: WeatherLocation, record: CurrentWeather) -> CurrentWeatherRead:
        return CurrentWeatherRead(
            provider=record.provider,
            location=self._location_read(location),
            observed_at=record.observed_at,
            fetched_at=record.fetched_at,
            temperature_c=record.temperature_c,
            humidity_percent=record.humidity_percent,
            rainfall_mm=record.rainfall_mm,
            wind_speed_kmh=record.wind_speed_kmh,
            pressure_hpa=record.pressure_hpa,
            cloud_cover_percent=record.cloud_cover_percent,
        )

    def _hourly_read(self, location: WeatherLocation, record: HourlyForecast) -> HourlyForecastRead:
        return HourlyForecastRead(
            provider=record.provider,
            location=self._location_read(location),
            forecast_time=record.forecast_time,
            fetched_at=record.fetched_at,
            temperature_c=record.temperature_c,
            humidity_percent=record.humidity_percent,
            rainfall_mm=record.rainfall_mm,
            wind_speed_kmh=record.wind_speed_kmh,
            pressure_hpa=record.pressure_hpa,
            cloud_cover_percent=record.cloud_cover_percent,
        )

    def _daily_read(self, location: WeatherLocation, record: DailyForecast) -> DailyForecastRead:
        return DailyForecastRead(
            provider=record.provider,
            location=self._location_read(location),
            forecast_date=record.forecast_date,
            fetched_at=record.fetched_at,
            temperature_min_c=record.temperature_min_c,
            temperature_max_c=record.temperature_max_c,
            humidity_percent=record.humidity_percent,
            rainfall_mm=record.rainfall_mm,
            wind_speed_kmh=record.wind_speed_kmh,
            pressure_hpa=record.pressure_hpa,
            cloud_cover_percent=record.cloud_cover_percent,
        )

    def _observation_read(self, location: WeatherLocation, record: WeatherObservation) -> WeatherObservationRead:
        return WeatherObservationRead(
            provider=record.provider,
            location=self._location_read(location),
            observed_at=record.observed_at,
            fetched_at=record.fetched_at,
            temperature_c=record.temperature_c,
            humidity_percent=record.humidity_percent,
            rainfall_mm=record.rainfall_mm,
            wind_speed_kmh=record.wind_speed_kmh,
            pressure_hpa=record.pressure_hpa,
            cloud_cover_percent=record.cloud_cover_percent,
        )

    def _cache_key(self, namespace: str, location: WeatherLocation, extra: str = "") -> str:
        location_key = f"farm:{location.farm_id}" if location.farm_id is not None else f"coord:{location.latitude}:{location.longitude}"
        return f"weather:{self.provider.name}:{namespace}:{location_key}:{extra}"


def _assign_metric_fields(
    record: HourlyForecast | WeatherObservation,
    item: HourlyForecastData | WeatherObservationData,
) -> None:
    record.temperature_c = item.temperature_c
    record.humidity_percent = item.humidity_percent
    record.rainfall_mm = item.rainfall_mm
    record.wind_speed_kmh = item.wind_speed_kmh
    record.pressure_hpa = item.pressure_hpa
    record.cloud_cover_percent = item.cloud_cover_percent


def _now() -> datetime:
    return datetime.now(timezone.utc)


weather_service = WeatherService()
