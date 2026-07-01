from __future__ import annotations

from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.disease import Crop, CropDisease, CropStage


class DiseaseSeed(TypedDict):
    name: str
    severity_scale: int


class CropSeed(TypedDict):
    name: str
    scientific_name: str
    stages: tuple[str, ...]
    diseases: tuple[DiseaseSeed, ...]


CROP_DISEASE_CATALOG: tuple[CropSeed, ...] = (
    {
        "name": "Rice",
        "scientific_name": "Oryza sativa",
        "stages": ("Seedling", "Tillering", "Panicle initiation", "Flowering", "Maturity"),
        "diseases": (
            {"name": "Blast", "severity_scale": 100},
            {"name": "Brown Spot", "severity_scale": 100},
        ),
    },
    {
        "name": "Wheat",
        "scientific_name": "Triticum aestivum",
        "stages": ("Tillering", "Stem elongation", "Booting", "Heading", "Grain filling"),
        "diseases": ({"name": "Rust", "severity_scale": 100},),
    },
    {
        "name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "stages": ("Emergence", "Vegetative growth", "Tuber initiation", "Tuber bulking", "Maturity"),
        "diseases": ({"name": "Late Blight", "severity_scale": 100},),
    },
    {
        "name": "Sugarcane",
        "scientific_name": "Saccharum officinarum",
        "stages": ("Germination", "Tillering", "Grand growth", "Maturity"),
        "diseases": ({"name": "Red Rot", "severity_scale": 100},),
    },
)


def seed_disease_catalog(session: Session, seeds: tuple[CropSeed, ...] = CROP_DISEASE_CATALOG) -> None:
    existing_crops = {crop.name: crop for crop in session.scalars(select(Crop)).all()}
    for crop_seed in seeds:
        crop = existing_crops.get(crop_seed["name"])
        if crop is None:
            crop = Crop(name=crop_seed["name"], scientific_name=crop_seed["scientific_name"])
            session.add(crop)
            session.flush()
            existing_crops[crop.name] = crop
        else:
            crop.scientific_name = crop_seed["scientific_name"]

        _seed_stages(session, crop, crop_seed["stages"])
        _seed_diseases(session, crop, crop_seed["diseases"])


def _seed_stages(session: Session, crop: Crop, stage_names: tuple[str, ...]) -> None:
    existing = {
        stage.name: stage
        for stage in session.scalars(select(CropStage).where(CropStage.crop_id == crop.id)).all()
    }
    for stage_name in stage_names:
        if stage_name not in existing:
            session.add(CropStage(crop_id=crop.id, name=stage_name))


def _seed_diseases(session: Session, crop: Crop, diseases: tuple[DiseaseSeed, ...]) -> None:
    existing = {
        disease.name: disease
        for disease in session.scalars(select(CropDisease).where(CropDisease.crop_id == crop.id)).all()
    }
    for disease_seed in diseases:
        disease = existing.get(disease_seed["name"])
        if disease is None:
            session.add(
                CropDisease(
                    crop_id=crop.id,
                    name=disease_seed["name"],
                    severity_scale=disease_seed["severity_scale"],
                )
            )
        else:
            disease.severity_scale = disease_seed["severity_scale"]
