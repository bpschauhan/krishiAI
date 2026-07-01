from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

SeasonType = Literal["Kharif", "Rabi", "Zaid"]


class CropSeasonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    crop_id: int
    crop_name: str
    season_name: str
    season_type: SeasonType


class CropCalendarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    crop_id: int
    crop_name: str
    district_id: int
    district_name: str
    sowing_start: date
    sowing_end: date
    harvest_start: date
    harvest_end: date


class CropSuitabilityResponse(BaseModel):
    farm_id: int
    crop_id: int
    crop_name: str
    district_id: int
    district_name: str
    suitability_score: int
    season: SeasonType
    weather_match: bool
    rainfall_match: bool
    temperature_match: bool
    created_at: datetime


class CropSuitabilityAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    crop_id: int
    suitability_score: int
    season: SeasonType
    created_at: datetime


class SuitabilityWeatherInput(BaseModel):
    temperature_c: Decimal | None = None
    rainfall_mm: Decimal
