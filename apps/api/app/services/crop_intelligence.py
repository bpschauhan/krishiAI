from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_intelligence import (
    CropCalendar,
    CropSeason,
    CropSuitabilityAssessment,
    CropSuitabilityProfile,
)
from app.models.disease import Crop
from app.models.farm import Farm
from app.models.geospatial import FarmBoundary
from app.models.location import District
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.schemas.crop_intelligence import CropCalendarRead, CropSeasonRead, CropSuitabilityResponse, SeasonType
from app.schemas.weather import WeatherQuery
from app.services.weather_service import WeatherService, weather_service


@dataclass(frozen=True)
class SuitabilityWeather:
    temperature_c: Decimal | None
    rainfall_mm: Decimal


@dataclass(frozen=True)
class CropSuitabilityResult:
    suitability_score: int
    weather_match: bool
    rainfall_match: bool
    temperature_match: bool


class SeasonResolver:
    def resolve(self, on_date: date | None = None) -> SeasonType:
        resolved = on_date or date.today()
        if resolved.month in (6, 7, 8, 9, 10):
            return "Kharif"
        if resolved.month in (11, 12, 1, 2, 3):
            return "Rabi"
        return "Zaid"


class CropSuitabilityEngine:
    def calculate(
        self,
        profile: CropSuitabilityProfile,
        weather: SuitabilityWeather,
        active_season: SeasonType,
        crop_seasons: list[CropSeason],
    ) -> CropSuitabilityResult:
        temperature_score = _range_score(weather.temperature_c, profile.min_temperature, profile.max_temperature)
        rainfall_score = _range_score(weather.rainfall_mm, profile.min_rainfall, profile.max_rainfall)
        season_score = 100 if any(season.season_type == active_season for season in crop_seasons) else 50
        suitability_score = int(round((temperature_score * 0.4) + (rainfall_score * 0.4) + (season_score * 0.2)))
        temperature_match = weather.temperature_c is not None and profile.min_temperature <= weather.temperature_c <= profile.max_temperature
        rainfall_match = profile.min_rainfall <= weather.rainfall_mm <= profile.max_rainfall
        return CropSuitabilityResult(
            suitability_score=max(0, min(100, suitability_score)),
            weather_match=temperature_match and rainfall_match,
            rainfall_match=rainfall_match,
            temperature_match=temperature_match,
        )


class CropSuitabilityHistoryService:
    def store(
        self,
        session: Session,
        farm_id: int,
        crop_id: int,
        result: CropSuitabilityResult,
        season: SeasonType,
    ) -> CropSuitabilityAssessment:
        assessment = CropSuitabilityAssessment(
            farm_id=farm_id,
            crop_id=crop_id,
            suitability_score=result.suitability_score,
            season=season,
        )
        session.add(assessment)
        session.commit()
        session.refresh(assessment)
        return assessment


class CropIntelligenceService:
    def __init__(
        self,
        resolver: SeasonResolver | None = None,
        engine: CropSuitabilityEngine | None = None,
        history: CropSuitabilityHistoryService | None = None,
        weather: WeatherService | None = None,
    ) -> None:
        self.resolver = resolver or SeasonResolver()
        self.engine = engine or CropSuitabilityEngine()
        self.history = history or CropSuitabilityHistoryService()
        self.weather = weather or weather_service

    def list_seasons(self, session: Session) -> list[CropSeasonRead]:
        rows = session.execute(select(CropSeason, Crop).join(Crop, Crop.id == CropSeason.crop_id).order_by(Crop.name)).all()
        return [
            CropSeasonRead(
                id=season.id,
                crop_id=season.crop_id,
                crop_name=crop.name,
                season_name=season.season_name,
                season_type=season.season_type,
            )
            for season, crop in rows
        ]

    def list_calendar(self, session: Session, district_id: int) -> list[CropCalendarRead]:
        district = session.get(District, district_id)
        if district is None:
            raise LookupError("District not found")
        rows = session.execute(
            select(CropCalendar, Crop, District)
            .join(Crop, Crop.id == CropCalendar.crop_id)
            .join(District, District.id == CropCalendar.district_id)
            .where(CropCalendar.district_id == district_id)
            .order_by(Crop.name)
        ).all()
        return [
            CropCalendarRead(
                id=calendar.id,
                crop_id=calendar.crop_id,
                crop_name=crop.name,
                district_id=calendar.district_id,
                district_name=row_district.name,
                sowing_start=calendar.sowing_start,
                sowing_end=calendar.sowing_end,
                harvest_start=calendar.harvest_start,
                harvest_end=calendar.harvest_end,
            )
            for calendar, crop, row_district in rows
        ]

    def assess_suitability(self, session: Session, farm_id: int, crop_id: int) -> CropSuitabilityResponse:
        farm = session.get(Farm, farm_id)
        if farm is None:
            raise LookupError("Farm not found")

        boundary = session.scalar(select(FarmBoundary).where(FarmBoundary.farm_id == farm_id).order_by(FarmBoundary.id))
        if boundary is None:
            raise LookupError("Farm boundary not found")

        crop = session.get(Crop, crop_id)
        if crop is None:
            raise LookupError("Crop not found")

        district = session.get(District, farm.district_id)
        if district is None:
            raise LookupError("District not found")

        profile = session.scalar(select(CropSuitabilityProfile).where(CropSuitabilityProfile.crop_id == crop_id))
        if profile is None:
            raise LookupError("Crop suitability profile not found")

        crop_seasons = session.scalars(select(CropSeason).where(CropSeason.crop_id == crop_id)).all()
        season = self.resolver.resolve()
        weather = self._weather_input(session, farm_id)
        result = self.engine.calculate(profile, weather, season, list(crop_seasons))
        assessment = self.history.store(session, farm_id, crop_id, result, season)
        return CropSuitabilityResponse(
            farm_id=farm_id,
            crop_id=crop_id,
            crop_name=crop.name,
            district_id=district.id,
            district_name=district.name,
            suitability_score=assessment.suitability_score,
            season=season,
            weather_match=result.weather_match,
            rainfall_match=result.rainfall_match,
            temperature_match=result.temperature_match,
            created_at=assessment.created_at or datetime.now(timezone.utc),
        )

    def _weather_input(self, session: Session, farm_id: int) -> SuitabilityWeather:
        location = session.scalar(select(WeatherLocation).where(WeatherLocation.farm_id == farm_id))
        if location is None:
            self.weather.current_weather(session, WeatherQuery(farm_id=farm_id))
            location = session.scalar(select(WeatherLocation).where(WeatherLocation.farm_id == farm_id))
        if location is None:
            raise LookupError("Weather location not found")

        current = session.scalar(
            select(CurrentWeather)
            .where(CurrentWeather.location_id == location.id)
            .order_by(CurrentWeather.observed_at.desc())
        )
        if current is None:
            self.weather.current_weather(session, WeatherQuery(farm_id=farm_id))
            current = session.scalar(
                select(CurrentWeather)
                .where(CurrentWeather.location_id == location.id)
                .order_by(CurrentWeather.observed_at.desc())
            )

        daily = session.scalar(
            select(DailyForecast)
            .where(DailyForecast.location_id == location.id)
            .order_by(DailyForecast.forecast_date.desc())
        )

        rainfall = current.rainfall_mm if current and current.rainfall_mm is not None else Decimal("0")
        if daily and daily.rainfall_mm is not None:
            rainfall = max(rainfall, daily.rainfall_mm)
        temperature = current.temperature_c if current else None
        if temperature is None and daily and daily.temperature_max_c is not None:
            temperature = daily.temperature_max_c
        return SuitabilityWeather(temperature_c=temperature, rainfall_mm=_round_mm(rainfall))


def _range_score(value: Decimal | None, minimum: Decimal, maximum: Decimal) -> int:
    if value is None:
        return 50
    if minimum <= value <= maximum:
        return 100
    if value < minimum:
        return _penalized_score(minimum - value)
    return _penalized_score(value - maximum)


def _penalized_score(distance: Decimal) -> int:
    return max(0, int(round(100 - (float(distance) * 5))))


def _round_mm(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


crop_intelligence_service = CropIntelligenceService()
