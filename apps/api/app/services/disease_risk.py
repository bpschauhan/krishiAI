from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.disease import Crop, CropDisease, CropStage, DiseaseRiskAssessment
from app.models.farm import Farm
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.schemas.disease import DiseaseRiskResponse, DiseaseRiskResult, RiskLevel
from app.schemas.weather import WeatherQuery
from app.services.weather_service import WeatherService, weather_service


@dataclass(frozen=True)
class WeatherRiskInput:
    temperature_c: float | None
    humidity_percent: float | None
    rainfall_mm: float | None


@dataclass(frozen=True)
class DiseaseRuleProfile:
    temperature_min_c: float
    temperature_max_c: float
    humidity_threshold_percent: float
    rainfall_threshold_mm: float
    susceptible_stages: tuple[str, ...]


@dataclass(frozen=True)
class DiseaseScore:
    score: int
    level: RiskLevel
    contributing_factors: list[str]


DEFAULT_RULE_PROFILES: dict[tuple[str, str], DiseaseRuleProfile] = {
    ("Rice", "Blast"): DiseaseRuleProfile(temperature_min_c=20, temperature_max_c=30, humidity_threshold_percent=85, rainfall_threshold_mm=2, susceptible_stages=("Tillering", "Panicle initiation", "Flowering")),
    ("Rice", "Brown Spot"): DiseaseRuleProfile(temperature_min_c=22, temperature_max_c=32, humidity_threshold_percent=75, rainfall_threshold_mm=1, susceptible_stages=("Tillering", "Maturity")),
    ("Wheat", "Rust"): DiseaseRuleProfile(temperature_min_c=15, temperature_max_c=25, humidity_threshold_percent=70, rainfall_threshold_mm=1, susceptible_stages=("Stem elongation", "Booting", "Heading")),
    ("Potato", "Late Blight"): DiseaseRuleProfile(temperature_min_c=10, temperature_max_c=22, humidity_threshold_percent=80, rainfall_threshold_mm=2, susceptible_stages=("Vegetative growth", "Tuber initiation", "Tuber bulking")),
    ("Sugarcane", "Red Rot"): DiseaseRuleProfile(temperature_min_c=25, temperature_max_c=35, humidity_threshold_percent=70, rainfall_threshold_mm=3, susceptible_stages=("Tillering", "Grand growth")),
}


class DiseaseRuleEngine:
    def __init__(self, profiles: dict[tuple[str, str], DiseaseRuleProfile] | None = None) -> None:
        self.profiles = profiles or DEFAULT_RULE_PROFILES

    def calculate_risk(
        self,
        crop: Crop,
        disease: CropDisease,
        crop_stage: CropStage,
        weather: WeatherRiskInput,
    ) -> DiseaseScore:
        profile = self.profiles.get((crop.name, disease.name), DiseaseRuleProfile(18, 32, 75, 1, (crop_stage.name,)))
        score = 10
        factors: list[str] = []

        if weather.temperature_c is not None:
            if profile.temperature_min_c <= weather.temperature_c <= profile.temperature_max_c:
                score += 30
                factors.append("temperature within disease-favorable range")
            else:
                distance = min(
                    abs(weather.temperature_c - profile.temperature_min_c),
                    abs(weather.temperature_c - profile.temperature_max_c),
                )
                if distance <= 3:
                    score += 15
                    factors.append("temperature near disease-favorable range")

        if weather.humidity_percent is not None and weather.humidity_percent >= profile.humidity_threshold_percent:
            score += 25
            factors.append("high humidity")

        if weather.rainfall_mm is not None and weather.rainfall_mm >= profile.rainfall_threshold_mm:
            score += 20
            factors.append("recent or forecast rainfall")

        if crop_stage.name in profile.susceptible_stages:
            score += 15
            factors.append("crop stage is susceptible")

        scaled_score = round(min(score, disease.severity_scale, 100))
        if not factors:
            factors.append("no major disease-favorable weather factors detected")

        return DiseaseScore(
            score=scaled_score,
            level=risk_level_for_score(scaled_score),
            contributing_factors=factors,
        )


class DiseaseRiskHistoryService:
    def store_assessments(
        self,
        session: Session,
        farm_id: int,
        crop_id: int,
        crop_stage_id: int,
        results: list[DiseaseRiskResult],
    ) -> list[DiseaseRiskAssessment]:
        records = [
            DiseaseRiskAssessment(
                farm_id=farm_id,
                crop_id=crop_id,
                crop_stage_id=crop_stage_id,
                disease_id=result.disease_id,
                score=Decimal(str(result.risk_score)),
                level=result.risk_level,
            )
            for result in results
        ]
        session.add_all(records)
        session.commit()
        for record in records:
            session.refresh(record)
        return records


class DiseaseRiskService:
    def __init__(
        self,
        rule_engine: DiseaseRuleEngine | None = None,
        history_service: DiseaseRiskHistoryService | None = None,
        weather: WeatherService | None = None,
    ) -> None:
        self.rule_engine = rule_engine or DiseaseRuleEngine()
        self.history_service = history_service or DiseaseRiskHistoryService()
        self.weather = weather or weather_service

    def assess_farm(self, session: Session, farm_id: int, crop_id: int, crop_stage_id: int) -> DiseaseRiskResponse:
        farm = session.get(Farm, farm_id)
        if farm is None:
            raise LookupError("Farm not found")

        crop = session.get(Crop, crop_id)
        if crop is None:
            raise LookupError("Crop not found")

        crop_stage = session.get(CropStage, crop_stage_id)
        if crop_stage is None or crop_stage.crop_id != crop_id:
            raise LookupError("Crop stage not found")

        diseases = list(session.scalars(select(CropDisease).where(CropDisease.crop_id == crop_id).order_by(CropDisease.name)))
        if not diseases:
            raise LookupError("No diseases configured for crop")

        weather_input = self._weather_input(session, farm_id)
        results = [
            self._result_for_disease(crop, disease, crop_stage, weather_input)
            for disease in diseases
        ]
        self.history_service.store_assessments(session, farm_id, crop_id, crop_stage_id, results)

        aggregate_score = round(sum(result.risk_score for result in results) / len(results))
        return DiseaseRiskResponse(
            farm_id=farm_id,
            crop_id=crop_id,
            crop_name=crop.name,
            crop_stage_id=crop_stage_id,
            crop_stage_name=crop_stage.name,
            risk_score=aggregate_score,
            risk_level=risk_level_for_score(aggregate_score),
            disease_results=results,
            assessed_at=datetime.now(timezone.utc),
        )

    def _weather_input(self, session: Session, farm_id: int) -> WeatherRiskInput:
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

        temperature = _to_float(current.temperature_c if current else None)
        humidity = _to_float(current.humidity_percent if current else None)
        rainfall = _to_float(current.rainfall_mm if current else None)
        if daily and daily.rainfall_mm is not None:
            rainfall = max(rainfall or 0, float(daily.rainfall_mm))
        return WeatherRiskInput(temperature_c=temperature, humidity_percent=humidity, rainfall_mm=rainfall)

    def _result_for_disease(
        self,
        crop: Crop,
        disease: CropDisease,
        crop_stage: CropStage,
        weather_input: WeatherRiskInput,
    ) -> DiseaseRiskResult:
        score = self.rule_engine.calculate_risk(crop, disease, crop_stage, weather_input)
        return DiseaseRiskResult(
            disease_id=disease.id,
            disease_name=disease.name,
            risk_score=score.score,
            risk_level=score.level,
            contributing_factors=score.contributing_factors,
        )


def risk_level_for_score(score: int) -> RiskLevel:
    if score <= 30:
        return "Low"
    if score <= 70:
        return "Medium"
    return "High"


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


disease_risk_service = DiseaseRiskService()
