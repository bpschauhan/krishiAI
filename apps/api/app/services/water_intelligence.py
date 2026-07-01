from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.disease import Crop, CropStage
from app.models.farm import Farm
from app.models.geospatial import FarmBoundary
from app.models.water import CropWaterProfile, FarmWaterRequirement, WaterAssessmentHistory
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.schemas.water import WaterIntelligenceResponse, WaterStatus
from app.schemas.weather import WeatherQuery
from app.services.weather_service import WeatherService, weather_service


@dataclass(frozen=True)
class WaterWeatherInput:
    rainfall_mm: Decimal
    temperature_c: Decimal | None


@dataclass(frozen=True)
class WaterRequirementResult:
    estimated_requirement_mm: Decimal
    rainfall_mm: Decimal
    deficit_mm: Decimal
    surplus_mm: Decimal
    status: WaterStatus


class WaterRequirementEngine:
    def calculate(
        self,
        profile: CropWaterProfile,
        weather: WaterWeatherInput,
    ) -> WaterRequirementResult:
        requirement = profile.optimal_mm_per_day
        if weather.temperature_c is not None:
            if weather.temperature_c >= Decimal("35"):
                requirement *= Decimal("1.20")
            elif weather.temperature_c >= Decimal("30"):
                requirement *= Decimal("1.10")
            elif weather.temperature_c <= Decimal("15"):
                requirement *= Decimal("0.90")

        requirement = min(max(requirement, profile.min_mm_per_day), profile.max_mm_per_day)
        requirement = _round_mm(requirement)
        rainfall = _round_mm(weather.rainfall_mm)
        deficit = _round_mm(max(requirement - rainfall, Decimal("0")))
        surplus = _round_mm(max(rainfall - requirement, Decimal("0")))
        return WaterRequirementResult(
            estimated_requirement_mm=requirement,
            rainfall_mm=rainfall,
            deficit_mm=deficit,
            surplus_mm=surplus,
            status=water_status(deficit, surplus),
        )


class WaterHistoryService:
    def store(
        self,
        session: Session,
        farm_id: int,
        crop_id: int,
        stage_id: int,
        result: WaterRequirementResult,
    ) -> FarmWaterRequirement:
        requirement = FarmWaterRequirement(
            farm_id=farm_id,
            crop_id=crop_id,
            stage_id=stage_id,
            estimated_requirement_mm=result.estimated_requirement_mm,
            rainfall_mm=result.rainfall_mm,
            deficit_mm=result.deficit_mm,
            surplus_mm=result.surplus_mm,
            status=result.status,
        )
        history = WaterAssessmentHistory(
            farm_id=farm_id,
            crop_id=crop_id,
            stage_id=stage_id,
            estimated_requirement_mm=result.estimated_requirement_mm,
            rainfall_mm=result.rainfall_mm,
            deficit_mm=result.deficit_mm,
            surplus_mm=result.surplus_mm,
            status=result.status,
        )
        session.add_all([requirement, history])
        session.commit()
        session.refresh(requirement)
        return requirement


class WaterIntelligenceService:
    def __init__(
        self,
        engine: WaterRequirementEngine | None = None,
        history: WaterHistoryService | None = None,
        weather: WeatherService | None = None,
    ) -> None:
        self.engine = engine or WaterRequirementEngine()
        self.history = history or WaterHistoryService()
        self.weather = weather or weather_service

    def assess_farm(self, session: Session, farm_id: int, crop_id: int, crop_stage_id: int) -> WaterIntelligenceResponse:
        farm = session.get(Farm, farm_id)
        if farm is None:
            raise LookupError("Farm not found")

        boundary = session.scalar(select(FarmBoundary).where(FarmBoundary.farm_id == farm_id).order_by(FarmBoundary.id))
        if boundary is None:
            raise LookupError("Farm boundary not found")

        crop = session.get(Crop, crop_id)
        if crop is None:
            raise LookupError("Crop not found")

        stage = session.get(CropStage, crop_stage_id)
        if stage is None or stage.crop_id != crop_id:
            raise LookupError("Crop stage not found")

        profile = session.scalar(
            select(CropWaterProfile).where(
                CropWaterProfile.crop_id == crop_id,
                CropWaterProfile.stage_id == crop_stage_id,
            )
        )
        if profile is None:
            raise LookupError("Water profile not found")

        weather_input = self._weather_input(session, farm_id)
        result = self.engine.calculate(profile, weather_input)
        requirement = self.history.store(session, farm_id, crop_id, crop_stage_id, result)
        return WaterIntelligenceResponse(
            farm_id=farm_id,
            crop_id=crop_id,
            crop_name=crop.name,
            crop_stage_id=crop_stage_id,
            crop_stage_name=stage.name,
            estimated_requirement_mm=requirement.estimated_requirement_mm,
            rainfall_mm=requirement.rainfall_mm,
            deficit_mm=requirement.deficit_mm,
            surplus_mm=requirement.surplus_mm,
            status=requirement.status,
            calculated_at=requirement.calculated_at or datetime.now(timezone.utc),
        )

    def _weather_input(self, session: Session, farm_id: int) -> WaterWeatherInput:
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
        return WaterWeatherInput(rainfall_mm=rainfall, temperature_c=temperature)


def water_status(deficit_mm: Decimal, surplus_mm: Decimal) -> WaterStatus:
    if deficit_mm > Decimal("0.10"):
        return "Deficit"
    if surplus_mm > Decimal("0.10"):
        return "Surplus"
    return "Adequate"


def _round_mm(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


water_intelligence_service = WaterIntelligenceService()
