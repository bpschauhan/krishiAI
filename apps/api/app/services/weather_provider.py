from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass(frozen=True)
class WeatherMetric:
    temperature_c: Decimal | None
    humidity_percent: Decimal | None
    rainfall_mm: Decimal | None
    wind_speed_kmh: Decimal | None
    pressure_hpa: Decimal | None
    cloud_cover_percent: Decimal | None


@dataclass(frozen=True)
class CurrentWeatherData(WeatherMetric):
    observed_at: datetime


@dataclass(frozen=True)
class HourlyForecastData(WeatherMetric):
    forecast_time: datetime


@dataclass(frozen=True)
class DailyForecastData:
    forecast_date: date
    temperature_min_c: Decimal | None
    temperature_max_c: Decimal | None
    humidity_percent: Decimal | None
    rainfall_mm: Decimal | None
    wind_speed_kmh: Decimal | None
    pressure_hpa: Decimal | None
    cloud_cover_percent: Decimal | None


@dataclass(frozen=True)
class WeatherObservationData(WeatherMetric):
    observed_at: datetime


class WeatherProvider(ABC):
    name: str

    @abstractmethod
    def current_weather(self, latitude: float, longitude: float) -> CurrentWeatherData:
        raise NotImplementedError

    @abstractmethod
    def hourly_forecast(self, latitude: float, longitude: float, hours: int = 24) -> list[HourlyForecastData]:
        raise NotImplementedError

    @abstractmethod
    def daily_forecast(self, latitude: float, longitude: float, days: int = 7) -> list[DailyForecastData]:
        raise NotImplementedError

    @abstractmethod
    def historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherObservationData]:
        raise NotImplementedError


class OpenMeteoProvider(WeatherProvider):
    name = "open-meteo"

    forecast_url = "https://api.open-meteo.com/v1/forecast"
    archive_url = "https://archive-api.open-meteo.com/v1/archive"

    def current_weather(self, latitude: float, longitude: float) -> CurrentWeatherData:
        payload = self._get_json(
            self.forecast_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "UTC",
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "rain",
                        "wind_speed_10m",
                        "surface_pressure",
                        "cloud_cover",
                    ]
                ),
            },
        )
        current = payload.get("current", {})
        return CurrentWeatherData(
            observed_at=_parse_datetime(current.get("time")),
            temperature_c=_decimal(current.get("temperature_2m")),
            humidity_percent=_decimal(current.get("relative_humidity_2m")),
            rainfall_mm=_decimal(current.get("rain")),
            wind_speed_kmh=_decimal(current.get("wind_speed_10m")),
            pressure_hpa=_decimal(current.get("surface_pressure")),
            cloud_cover_percent=_decimal(current.get("cloud_cover")),
        )

    def hourly_forecast(self, latitude: float, longitude: float, hours: int = 24) -> list[HourlyForecastData]:
        payload = self._get_json(
            self.forecast_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "UTC",
                "forecast_days": max(1, min((hours + 23) // 24, 16)),
                "hourly": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "rain",
                        "wind_speed_10m",
                        "surface_pressure",
                        "cloud_cover",
                    ]
                ),
            },
        )
        hourly = payload.get("hourly", {})
        records = []
        for index, time_value in enumerate(hourly.get("time", [])[:hours]):
            records.append(
                HourlyForecastData(
                    forecast_time=_parse_datetime(time_value),
                    temperature_c=_decimal_at(hourly, "temperature_2m", index),
                    humidity_percent=_decimal_at(hourly, "relative_humidity_2m", index),
                    rainfall_mm=_decimal_at(hourly, "rain", index),
                    wind_speed_kmh=_decimal_at(hourly, "wind_speed_10m", index),
                    pressure_hpa=_decimal_at(hourly, "surface_pressure", index),
                    cloud_cover_percent=_decimal_at(hourly, "cloud_cover", index),
                )
            )
        return records

    def daily_forecast(self, latitude: float, longitude: float, days: int = 7) -> list[DailyForecastData]:
        payload = self._get_json(
            self.forecast_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "UTC",
                "forecast_days": max(1, min(days, 16)),
                "daily": ",".join(
                    [
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "rain_sum",
                        "wind_speed_10m_max",
                    ]
                ),
            },
        )
        daily = payload.get("daily", {})
        return [
            DailyForecastData(
                forecast_date=date.fromisoformat(time_value),
                temperature_min_c=_decimal_at(daily, "temperature_2m_min", index),
                temperature_max_c=_decimal_at(daily, "temperature_2m_max", index),
                humidity_percent=None,
                rainfall_mm=_decimal_at(daily, "rain_sum", index),
                wind_speed_kmh=_decimal_at(daily, "wind_speed_10m_max", index),
                pressure_hpa=None,
                cloud_cover_percent=None,
            )
            for index, time_value in enumerate(daily.get("time", [])[:days])
        ]

    def historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherObservationData]:
        payload = self._get_json(
            self.archive_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "UTC",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "hourly": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "rain",
                        "wind_speed_10m",
                        "surface_pressure",
                        "cloud_cover",
                    ]
                ),
            },
        )
        hourly = payload.get("hourly", {})
        return [
            WeatherObservationData(
                observed_at=_parse_datetime(time_value),
                temperature_c=_decimal_at(hourly, "temperature_2m", index),
                humidity_percent=_decimal_at(hourly, "relative_humidity_2m", index),
                rainfall_mm=_decimal_at(hourly, "rain", index),
                wind_speed_kmh=_decimal_at(hourly, "wind_speed_10m", index),
                pressure_hpa=_decimal_at(hourly, "surface_pressure", index),
                cloud_cover_percent=_decimal_at(hourly, "cloud_cover", index),
            )
            for index, time_value in enumerate(hourly.get("time", []))
        ]

    def _get_json(self, url: str, params: dict[str, object]) -> dict[str, Any]:
        request_url = f"{url}?{urlencode(params)}"
        with urlopen(request_url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


def _parse_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _decimal_at(payload: dict[str, Any], key: str, index: int) -> Decimal | None:
    values = payload.get(key)
    if not isinstance(values, list) or index >= len(values):
        return None
    return _decimal(values[index])
