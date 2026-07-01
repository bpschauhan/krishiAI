from __future__ import annotations

import json
from typing import Any, TypedDict

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.geospatial import GeoRegion


class RegionSeed(TypedDict):
    region_type: str
    name: str
    geometry: dict[str, Any]
    children: tuple["RegionSeed", ...]


INDIA_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[68.0, 6.0], [97.5, 6.0], [97.5, 37.5], [68.0, 37.5], [68.0, 6.0]]],
}

UTTAR_PRADESH_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[77.0, 23.5], [84.8, 23.5], [84.8, 30.6], [77.0, 30.6], [77.0, 23.5]]],
}

LUCKNOW_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[80.55, 26.55], [81.25, 26.55], [81.25, 27.15], [80.55, 27.15], [80.55, 26.55]]],
}

BAKSHI_KA_TALAB_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[80.78, 26.92], [81.05, 26.92], [81.05, 27.08], [80.78, 27.08], [80.78, 26.92]]],
}

SEMRA_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[80.90, 26.94], [80.98, 26.94], [80.98, 27.00], [80.90, 27.00], [80.90, 26.94]]],
}

REGION_SEED_HIERARCHY: tuple[RegionSeed, ...] = (
    {
        "region_type": "country",
        "name": "India",
        "geometry": INDIA_POLYGON,
        "children": (
            {
                "region_type": "state",
                "name": "Uttar Pradesh",
                "geometry": UTTAR_PRADESH_POLYGON,
                "children": (
                    {
                        "region_type": "district",
                        "name": "Lucknow",
                        "geometry": LUCKNOW_POLYGON,
                        "children": (
                            {
                                "region_type": "block",
                                "name": "Bakshi Ka Talab",
                                "geometry": BAKSHI_KA_TALAB_POLYGON,
                                "children": (
                                    {
                                        "region_type": "village",
                                        "name": "Semra",
                                        "geometry": SEMRA_POLYGON,
                                        "children": (),
                                    },
                                ),
                            },
                        ),
                    },
                ),
            },
        ),
    },
)


def seed_geo_regions(session: Session, seeds: tuple[RegionSeed, ...] = REGION_SEED_HIERARCHY) -> None:
    for seed in seeds:
        _upsert_region(session, seed, parent_id=None)


def _upsert_region(session: Session, seed: RegionSeed, parent_id: int | None) -> int:
    if session.get_bind().dialect.name == "postgresql":
        region_id = _upsert_region_postgresql(session, seed, parent_id)
    else:
        region_id = _upsert_region_orm(session, seed, parent_id)

    for child in seed["children"]:
        _upsert_region(session, child, parent_id=region_id)
    return region_id


def _upsert_region_orm(session: Session, seed: RegionSeed, parent_id: int | None) -> int:
    existing = session.scalar(
        select(GeoRegion).where(
            GeoRegion.region_type == seed["region_type"],
            GeoRegion.name == seed["name"],
            GeoRegion.parent_id == parent_id,
        )
    )
    geometry_json = json.dumps(seed["geometry"], separators=(",", ":"))
    if existing is None:
        existing = GeoRegion(
            region_type=seed["region_type"],
            name=seed["name"],
            parent_id=parent_id,
            geometry=geometry_json,
        )
        session.add(existing)
    else:
        existing.geometry = geometry_json
    session.flush()
    return existing.id


def _upsert_region_postgresql(session: Session, seed: RegionSeed, parent_id: int | None) -> int:
    existing_id = session.execute(
        text(
            """
            select id from geo_regions
            where region_type = :region_type
                and name = :name
                and parent_id is not distinct from :parent_id
            """
        ),
        {"region_type": seed["region_type"], "name": seed["name"], "parent_id": parent_id},
    ).scalar_one_or_none()
    geometry_json = json.dumps(seed["geometry"], separators=(",", ":"))
    params = {
        "region_type": seed["region_type"],
        "name": seed["name"],
        "parent_id": parent_id,
        "geometry": geometry_json,
    }
    if existing_id is None:
        return int(
            session.execute(
                text(
                    """
                    insert into geo_regions (region_type, name, parent_id, geometry)
                    values (:region_type, :name, :parent_id, ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326))
                    returning id
                    """
                ),
                params,
            ).scalar_one()
        )

    session.execute(
        text(
            """
            update geo_regions
            set geometry = ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                updated_at = now()
            where id = :id
            """
        ),
        {**params, "id": existing_id},
    )
    return int(existing_id)
