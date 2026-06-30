from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.farm import Farm
from app.models.geospatial import FarmBoundary, GeoRegion, PlotBoundary
from app.models.plot import Plot
from app.schemas.geospatial import (
    FarmBoundaryCreate,
    FarmBoundaryRead,
    FarmBoundaryUpdate,
    GeoRegionRead,
    PlotBoundaryCreate,
    PlotBoundaryRead,
    PlotBoundaryUpdate,
)
from app.utils.geo import calculate_polygon_area

router = APIRouter()


@router.post("/farm-boundaries", response_model=FarmBoundaryRead, status_code=status.HTTP_201_CREATED)
def create_farm_boundary(payload: FarmBoundaryCreate, db: Session = Depends(get_db)) -> FarmBoundaryRead:
    _get_required(db, Farm, payload.farm_id, "Farm")
    area = calculate_polygon_area(payload.geometry["coordinates"])
    geometry_json = json.dumps(payload.geometry, separators=(",", ":"))

    if _is_postgresql(db):
        row = db.execute(
            text(
                """
                insert into farm_boundaries
                    (farm_id, geometry, area_square_meters, area_hectares, area_acres)
                values
                    (:farm_id, ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                     :area_square_meters, :area_hectares, :area_acres)
                returning id, farm_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                """
            ),
            {
                "farm_id": payload.farm_id,
                "geometry": geometry_json,
                "area_square_meters": area.square_meters,
                "area_hectares": area.hectares,
                "area_acres": area.acres,
            },
        ).mappings().one()
        db.commit()
        return _farm_boundary_from_mapping(row)

    boundary = FarmBoundary(
        farm_id=payload.farm_id,
        geometry=geometry_json,
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
    db.add(boundary)
    db.commit()
    db.refresh(boundary)
    return _farm_boundary_from_model(boundary)


@router.get("/farm-boundaries/{boundary_id}", response_model=FarmBoundaryRead)
def get_farm_boundary(boundary_id: int, db: Session = Depends(get_db)) -> FarmBoundaryRead:
    if _is_postgresql(db):
        row = db.execute(
            text(
                """
                select id, farm_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                from farm_boundaries
                where id = :boundary_id
                """
            ),
            {"boundary_id": boundary_id},
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm boundary not found")
        return _farm_boundary_from_mapping(row)

    boundary = db.get(FarmBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm boundary not found")
    return _farm_boundary_from_model(boundary)


@router.put("/farm-boundaries/{boundary_id}", response_model=FarmBoundaryRead)
def update_farm_boundary(
    boundary_id: int,
    payload: FarmBoundaryUpdate,
    db: Session = Depends(get_db),
) -> FarmBoundaryRead:
    area = calculate_polygon_area(payload.geometry["coordinates"])
    geometry_json = json.dumps(payload.geometry, separators=(",", ":"))

    if _is_postgresql(db):
        existing = db.execute(
            text("select farm_id from farm_boundaries where id = :boundary_id"),
            {"boundary_id": boundary_id},
        ).mappings().first()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm boundary not found")
        _get_required(db, Farm, existing["farm_id"], "Farm")
        row = db.execute(
            text(
                """
                update farm_boundaries
                set geometry = ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                    area_square_meters = :area_square_meters,
                    area_hectares = :area_hectares,
                    area_acres = :area_acres,
                    updated_at = now()
                where id = :boundary_id
                returning id, farm_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                """
            ),
            {
                "boundary_id": boundary_id,
                "geometry": geometry_json,
                "area_square_meters": area.square_meters,
                "area_hectares": area.hectares,
                "area_acres": area.acres,
            },
        ).mappings().one()
        db.commit()
        return _farm_boundary_from_mapping(row)

    boundary = db.get(FarmBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm boundary not found")
    _get_required(db, Farm, boundary.farm_id, "Farm")
    _apply_boundary_measurement(boundary, geometry_json, area)
    db.commit()
    db.refresh(boundary)
    return _farm_boundary_from_model(boundary)


@router.delete("/farm-boundaries/{boundary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_boundary(boundary_id: int, db: Session = Depends(get_db)) -> None:
    boundary = db.get(FarmBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm boundary not found")
    db.delete(boundary)
    db.commit()


@router.get("/farms/{farm_id}/boundaries", response_model=list[FarmBoundaryRead])
def list_farm_boundaries(
    farm_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[FarmBoundaryRead]:
    _get_required(db, Farm, farm_id, "Farm")

    if _is_postgresql(db):
        rows = db.execute(
            text(
                """
                select id, farm_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                from farm_boundaries
                where farm_id = :farm_id
                order by id
                limit :limit
                offset :offset
                """
            ),
            {"farm_id": farm_id, "offset": offset, "limit": limit},
        ).mappings()
        return [_farm_boundary_from_mapping(row) for row in rows]

    statement = (
        select(FarmBoundary)
        .where(FarmBoundary.farm_id == farm_id)
        .order_by(FarmBoundary.id)
        .offset(offset)
        .limit(limit)
    )
    return [_farm_boundary_from_model(boundary) for boundary in db.scalars(statement)]


@router.post("/plot-boundaries", response_model=PlotBoundaryRead, status_code=status.HTTP_201_CREATED)
def create_plot_boundary(payload: PlotBoundaryCreate, db: Session = Depends(get_db)) -> PlotBoundaryRead:
    _get_required(db, Plot, payload.plot_id, "Plot")
    area = calculate_polygon_area(payload.geometry["coordinates"])
    geometry_json = json.dumps(payload.geometry, separators=(",", ":"))

    if _is_postgresql(db):
        row = db.execute(
            text(
                """
                insert into plot_boundaries
                    (plot_id, geometry, area_square_meters, area_hectares, area_acres)
                values
                    (:plot_id, ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                     :area_square_meters, :area_hectares, :area_acres)
                returning id, plot_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                """
            ),
            {
                "plot_id": payload.plot_id,
                "geometry": geometry_json,
                "area_square_meters": area.square_meters,
                "area_hectares": area.hectares,
                "area_acres": area.acres,
            },
        ).mappings().one()
        db.commit()
        return _plot_boundary_from_mapping(row)

    boundary = PlotBoundary(
        plot_id=payload.plot_id,
        geometry=geometry_json,
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
    db.add(boundary)
    db.commit()
    db.refresh(boundary)
    return _plot_boundary_from_model(boundary)


@router.get("/plot-boundaries/{boundary_id}", response_model=PlotBoundaryRead)
def get_plot_boundary(boundary_id: int, db: Session = Depends(get_db)) -> PlotBoundaryRead:
    if _is_postgresql(db):
        row = db.execute(
            text(
                """
                select id, plot_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                from plot_boundaries
                where id = :boundary_id
                """
            ),
            {"boundary_id": boundary_id},
        ).mappings().first()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot boundary not found")
        return _plot_boundary_from_mapping(row)

    boundary = db.get(PlotBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot boundary not found")
    return _plot_boundary_from_model(boundary)


@router.put("/plot-boundaries/{boundary_id}", response_model=PlotBoundaryRead)
def update_plot_boundary(
    boundary_id: int,
    payload: PlotBoundaryUpdate,
    db: Session = Depends(get_db),
) -> PlotBoundaryRead:
    area = calculate_polygon_area(payload.geometry["coordinates"])
    geometry_json = json.dumps(payload.geometry, separators=(",", ":"))

    if _is_postgresql(db):
        existing = db.execute(
            text("select plot_id from plot_boundaries where id = :boundary_id"),
            {"boundary_id": boundary_id},
        ).mappings().first()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot boundary not found")
        _get_required(db, Plot, existing["plot_id"], "Plot")
        row = db.execute(
            text(
                """
                update plot_boundaries
                set geometry = ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326),
                    area_square_meters = :area_square_meters,
                    area_hectares = :area_hectares,
                    area_acres = :area_acres,
                    updated_at = now()
                where id = :boundary_id
                returning id, plot_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                """
            ),
            {
                "boundary_id": boundary_id,
                "geometry": geometry_json,
                "area_square_meters": area.square_meters,
                "area_hectares": area.hectares,
                "area_acres": area.acres,
            },
        ).mappings().one()
        db.commit()
        return _plot_boundary_from_mapping(row)

    boundary = db.get(PlotBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot boundary not found")
    _get_required(db, Plot, boundary.plot_id, "Plot")
    _apply_boundary_measurement(boundary, geometry_json, area)
    db.commit()
    db.refresh(boundary)
    return _plot_boundary_from_model(boundary)


@router.delete("/plot-boundaries/{boundary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot_boundary(boundary_id: int, db: Session = Depends(get_db)) -> None:
    boundary = db.get(PlotBoundary, boundary_id)
    if boundary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot boundary not found")
    db.delete(boundary)
    db.commit()


@router.get("/plots/{plot_id}/boundaries", response_model=list[PlotBoundaryRead])
def list_plot_boundaries(
    plot_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PlotBoundaryRead]:
    _get_required(db, Plot, plot_id, "Plot")

    if _is_postgresql(db):
        rows = db.execute(
            text(
                """
                select id, plot_id, ST_AsGeoJSON(geometry) as geometry,
                    area_square_meters, area_hectares, area_acres, created_at, updated_at
                from plot_boundaries
                where plot_id = :plot_id
                order by id
                limit :limit
                offset :offset
                """
            ),
            {"plot_id": plot_id, "offset": offset, "limit": limit},
        ).mappings()
        return [_plot_boundary_from_mapping(row) for row in rows]

    statement = (
        select(PlotBoundary)
        .where(PlotBoundary.plot_id == plot_id)
        .order_by(PlotBoundary.id)
        .offset(offset)
        .limit(limit)
    )
    return [_plot_boundary_from_model(boundary) for boundary in db.scalars(statement)]


@router.get("/geo-regions", response_model=list[GeoRegionRead])
def list_geo_regions(
    region_type: str | None = Query(default=None),
    parent_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[GeoRegionRead]:
    if _is_postgresql(db):
        clauses = []
        params: dict[str, Any] = {}
        if region_type:
            clauses.append("region_type = :region_type")
            params["region_type"] = region_type
        if parent_id is not None:
            clauses.append("parent_id = :parent_id")
            params["parent_id"] = parent_id
        where_clause = f"where {' and '.join(clauses)}" if clauses else ""
        rows = db.execute(
            text(
                f"""
                select id, region_type, name, parent_id, ST_AsGeoJSON(geometry) as geometry,
                    created_at, updated_at
                from geo_regions
                {where_clause}
                order by region_type, name
                """
            ),
            params,
        ).mappings()
        return [_geo_region_from_mapping(row) for row in rows]

    statement = select(GeoRegion).order_by(GeoRegion.region_type, GeoRegion.name)
    if region_type:
        statement = statement.where(GeoRegion.region_type == region_type)
    if parent_id is not None:
        statement = statement.where(GeoRegion.parent_id == parent_id)
    return [_geo_region_from_model(region) for region in db.scalars(statement)]


def _get_required(db: Session, model: type[Farm] | type[Plot], item_id: int, name: str) -> None:
    if db.get(model, item_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


def _is_postgresql(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"


def _load_geometry(value: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(value)


def _apply_boundary_measurement(
    boundary: FarmBoundary | PlotBoundary,
    geometry_json: str,
    area: Any,
) -> None:
    boundary.geometry = geometry_json
    boundary.area_square_meters = Decimal(str(round(area.square_meters, 2)))
    boundary.area_hectares = Decimal(str(round(area.hectares, 4)))
    boundary.area_acres = Decimal(str(round(area.acres, 4)))


def _farm_boundary_from_model(boundary: FarmBoundary) -> FarmBoundaryRead:
    return FarmBoundaryRead(
        id=boundary.id,
        farm_id=boundary.farm_id,
        geometry=_load_geometry(boundary.geometry),
        area_square_meters=boundary.area_square_meters,
        area_hectares=boundary.area_hectares,
        area_acres=boundary.area_acres,
        created_at=boundary.created_at,
        updated_at=boundary.updated_at,
    )


def _farm_boundary_from_mapping(row: Any) -> FarmBoundaryRead:
    return FarmBoundaryRead(
        id=row["id"],
        farm_id=row["farm_id"],
        geometry=_load_geometry(row["geometry"]),
        area_square_meters=row["area_square_meters"],
        area_hectares=row["area_hectares"],
        area_acres=row["area_acres"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _plot_boundary_from_model(boundary: PlotBoundary) -> PlotBoundaryRead:
    return PlotBoundaryRead(
        id=boundary.id,
        plot_id=boundary.plot_id,
        geometry=_load_geometry(boundary.geometry),
        area_square_meters=boundary.area_square_meters,
        area_hectares=boundary.area_hectares,
        area_acres=boundary.area_acres,
        created_at=boundary.created_at,
        updated_at=boundary.updated_at,
    )


def _plot_boundary_from_mapping(row: Any) -> PlotBoundaryRead:
    return PlotBoundaryRead(
        id=row["id"],
        plot_id=row["plot_id"],
        geometry=_load_geometry(row["geometry"]),
        area_square_meters=row["area_square_meters"],
        area_hectares=row["area_hectares"],
        area_acres=row["area_acres"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _geo_region_from_model(region: GeoRegion) -> GeoRegionRead:
    return GeoRegionRead(
        id=region.id,
        region_type=region.region_type,
        name=region.name,
        parent_id=region.parent_id,
        geometry=_load_geometry(region.geometry),
        created_at=region.created_at,
        updated_at=region.updated_at,
    )


def _geo_region_from_mapping(row: Any) -> GeoRegionRead:
    return GeoRegionRead(
        id=row["id"],
        region_type=row["region_type"],
        name=row["name"],
        parent_id=row["parent_id"],
        geometry=_load_geometry(row["geometry"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
