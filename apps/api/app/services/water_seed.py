from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.disease import Crop, CropStage
from app.models.water import CropWaterProfile


class WaterProfileSeed(TypedDict):
    crop: str
    stage: str
    min_mm_per_day: str
    optimal_mm_per_day: str
    max_mm_per_day: str


WATER_PROFILE_CATALOG: tuple[WaterProfileSeed, ...] = (
    {"crop": "Rice", "stage": "Seedling", "min_mm_per_day": "4.00", "optimal_mm_per_day": "5.50", "max_mm_per_day": "7.00"},
    {"crop": "Rice", "stage": "Tillering", "min_mm_per_day": "5.00", "optimal_mm_per_day": "7.00", "max_mm_per_day": "9.00"},
    {"crop": "Rice", "stage": "Flowering", "min_mm_per_day": "6.00", "optimal_mm_per_day": "8.00", "max_mm_per_day": "10.00"},
    {"crop": "Wheat", "stage": "Tillering", "min_mm_per_day": "2.50", "optimal_mm_per_day": "4.00", "max_mm_per_day": "5.50"},
    {"crop": "Wheat", "stage": "Heading", "min_mm_per_day": "3.50", "optimal_mm_per_day": "5.00", "max_mm_per_day": "6.50"},
    {"crop": "Potato", "stage": "Vegetative growth", "min_mm_per_day": "3.50", "optimal_mm_per_day": "5.50", "max_mm_per_day": "7.00"},
    {"crop": "Potato", "stage": "Tuber bulking", "min_mm_per_day": "4.50", "optimal_mm_per_day": "6.50", "max_mm_per_day": "8.00"},
    {"crop": "Sugarcane", "stage": "Tillering", "min_mm_per_day": "4.50", "optimal_mm_per_day": "6.50", "max_mm_per_day": "8.50"},
    {"crop": "Sugarcane", "stage": "Grand growth", "min_mm_per_day": "6.00", "optimal_mm_per_day": "8.50", "max_mm_per_day": "11.00"},
)


def seed_water_profiles(session: Session, seeds: tuple[WaterProfileSeed, ...] = WATER_PROFILE_CATALOG) -> None:
    for seed in seeds:
        crop = session.scalar(select(Crop).where(Crop.name == seed["crop"]))
        if crop is None:
            continue
        stage = session.scalar(
            select(CropStage).where(CropStage.crop_id == crop.id, CropStage.name == seed["stage"])
        )
        if stage is None:
            continue

        profile = session.scalar(
            select(CropWaterProfile).where(
                CropWaterProfile.crop_id == crop.id,
                CropWaterProfile.stage_id == stage.id,
            )
        )
        if profile is None:
            profile = CropWaterProfile(crop_id=crop.id, stage_id=stage.id)
            session.add(profile)

        profile.min_mm_per_day = Decimal(seed["min_mm_per_day"])
        profile.optimal_mm_per_day = Decimal(seed["optimal_mm_per_day"])
        profile.max_mm_per_day = Decimal(seed["max_mm_per_day"])
