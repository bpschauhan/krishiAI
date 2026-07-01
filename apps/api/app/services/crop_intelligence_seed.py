from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_intelligence import CropCalendar, CropSeason, CropSuitabilityProfile
from app.models.disease import Crop
from app.models.location import District


class CropKnowledgeSeed(TypedDict):
    name: str
    scientific_name: str
    season_type: str
    min_temperature: str
    max_temperature: str
    min_rainfall: str
    max_rainfall: str
    preferred_soil_type: str
    sowing_start: date
    sowing_end: date
    harvest_start: date
    harvest_end: date


CROP_KNOWLEDGE_CATALOG: tuple[CropKnowledgeSeed, ...] = (
    {
        "name": "Rice",
        "scientific_name": "Oryza sativa",
        "season_type": "Kharif",
        "min_temperature": "20.00",
        "max_temperature": "38.00",
        "min_rainfall": "4.00",
        "max_rainfall": "12.00",
        "preferred_soil_type": "Clay loam",
        "sowing_start": date(2026, 6, 15),
        "sowing_end": date(2026, 7, 31),
        "harvest_start": date(2026, 10, 15),
        "harvest_end": date(2026, 11, 30),
    },
    {
        "name": "Wheat",
        "scientific_name": "Triticum aestivum",
        "season_type": "Rabi",
        "min_temperature": "10.00",
        "max_temperature": "28.00",
        "min_rainfall": "1.00",
        "max_rainfall": "5.00",
        "preferred_soil_type": "Loam",
        "sowing_start": date(2026, 11, 1),
        "sowing_end": date(2026, 12, 15),
        "harvest_start": date(2027, 3, 15),
        "harvest_end": date(2027, 4, 30),
    },
    {
        "name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "season_type": "Rabi",
        "min_temperature": "12.00",
        "max_temperature": "30.00",
        "min_rainfall": "1.00",
        "max_rainfall": "6.00",
        "preferred_soil_type": "Sandy loam",
        "sowing_start": date(2026, 10, 15),
        "sowing_end": date(2026, 11, 30),
        "harvest_start": date(2027, 1, 15),
        "harvest_end": date(2027, 3, 15),
    },
    {
        "name": "Sugarcane",
        "scientific_name": "Saccharum officinarum",
        "season_type": "Zaid",
        "min_temperature": "20.00",
        "max_temperature": "38.00",
        "min_rainfall": "3.00",
        "max_rainfall": "10.00",
        "preferred_soil_type": "Deep loam",
        "sowing_start": date(2026, 2, 15),
        "sowing_end": date(2026, 4, 30),
        "harvest_start": date(2027, 1, 1),
        "harvest_end": date(2027, 3, 31),
    },
    {
        "name": "Maize",
        "scientific_name": "Zea mays",
        "season_type": "Kharif",
        "min_temperature": "18.00",
        "max_temperature": "35.00",
        "min_rainfall": "2.00",
        "max_rainfall": "8.00",
        "preferred_soil_type": "Well-drained loam",
        "sowing_start": date(2026, 6, 15),
        "sowing_end": date(2026, 7, 20),
        "harvest_start": date(2026, 9, 15),
        "harvest_end": date(2026, 10, 31),
    },
    {
        "name": "Mustard",
        "scientific_name": "Brassica juncea",
        "season_type": "Rabi",
        "min_temperature": "10.00",
        "max_temperature": "30.00",
        "min_rainfall": "0.50",
        "max_rainfall": "4.00",
        "preferred_soil_type": "Loam",
        "sowing_start": date(2026, 10, 15),
        "sowing_end": date(2026, 11, 30),
        "harvest_start": date(2027, 2, 15),
        "harvest_end": date(2027, 3, 31),
    },
)


def seed_crop_intelligence_catalog(
    session: Session,
    seeds: tuple[CropKnowledgeSeed, ...] = CROP_KNOWLEDGE_CATALOG,
) -> None:
    district = session.scalar(select(District).where(District.name == "Lucknow", District.state == "Uttar Pradesh"))
    for seed in seeds:
        crop = session.scalar(select(Crop).where(Crop.name == seed["name"]))
        if crop is None:
            crop = Crop(name=seed["name"], scientific_name=seed["scientific_name"])
            session.add(crop)
            session.flush()
        elif crop.scientific_name is None:
            crop.scientific_name = seed["scientific_name"]

        _seed_season(session, crop, seed)
        _seed_profile(session, crop, seed)
        if district is not None:
            _seed_calendar(session, crop, district, seed)


def _seed_season(session: Session, crop: Crop, seed: CropKnowledgeSeed) -> None:
    season = session.scalar(
        select(CropSeason).where(CropSeason.crop_id == crop.id, CropSeason.season_type == seed["season_type"])
    )
    if season is None:
        season = CropSeason(crop_id=crop.id, season_type=seed["season_type"])
        session.add(season)
    season.season_name = f"{seed['name']} {seed['season_type']}"


def _seed_profile(session: Session, crop: Crop, seed: CropKnowledgeSeed) -> None:
    profile = session.scalar(select(CropSuitabilityProfile).where(CropSuitabilityProfile.crop_id == crop.id))
    if profile is None:
        profile = CropSuitabilityProfile(crop_id=crop.id)
        session.add(profile)
    profile.min_temperature = Decimal(seed["min_temperature"])
    profile.max_temperature = Decimal(seed["max_temperature"])
    profile.min_rainfall = Decimal(seed["min_rainfall"])
    profile.max_rainfall = Decimal(seed["max_rainfall"])
    profile.preferred_soil_type = seed["preferred_soil_type"]


def _seed_calendar(session: Session, crop: Crop, district: District, seed: CropKnowledgeSeed) -> None:
    calendar = session.scalar(
        select(CropCalendar).where(CropCalendar.crop_id == crop.id, CropCalendar.district_id == district.id)
    )
    if calendar is None:
        calendar = CropCalendar(crop_id=crop.id, district_id=district.id)
        session.add(calendar)
    calendar.sowing_start = seed["sowing_start"]
    calendar.sowing_end = seed["sowing_end"]
    calendar.harvest_start = seed["harvest_start"]
    calendar.harvest_end = seed["harvest_end"]
