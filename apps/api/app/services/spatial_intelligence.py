from __future__ import annotations

import json
from dataclasses import dataclass
from math import atan2, cos, pi, radians, sin, sqrt
from typing import Any, Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.farm import Farm
from app.models.geospatial import FarmBoundary, GeoRegion, PlotBoundary
from app.models.plot import Plot
from app.schemas.spatial import (
    BBoxSearchResponse,
    IntersectionResult,
    IntersectionsResponse,
    NearbyResponse,
    PointLookupResponse,
    RegionHierarchyResponse,
    SpatialBoundaryResult,
    SpatialMetrics,
    SpatialRegionResult,
)
from app.services.spatial import boundary_bbox, boundary_contains_point, boundary_intersects
from app.utils.geo import EARTH_RADIUS_METERS, calculate_polygon_area, parse_geojson_polygon

BoundaryKind = Literal["farm", "plot"]
REGION_ORDER = ("country", "state", "district", "block", "village")


@dataclass(frozen=True)
class Point:
    longitude: float
    latitude: float


def point_lookup(session: Session, longitude: float, latitude: float) -> PointLookupResponse:
    if _is_postgresql(session):
        return _point_lookup_postgresql(session, longitude, latitude)

    point = Point(longitude=longitude, latitude=latitude)
    return PointLookupResponse(
        farm_boundaries=[
            _farm_boundary_result(session, boundary)
            for boundary in session.scalars(select(FarmBoundary).order_by(FarmBoundary.id))
            if point_in_polygon(boundary.geometry, point)
        ],
        plot_boundaries=[
            _plot_boundary_result(session, boundary)
            for boundary in session.scalars(select(PlotBoundary).order_by(PlotBoundary.id))
            if point_in_polygon(boundary.geometry, point)
        ],
        regions=[
            _region_result(region)
            for region in session.scalars(select(GeoRegion).order_by(GeoRegion.id))
            if point_in_polygon(region.geometry, point)
        ],
    )


def nearest_boundaries(
    session: Session,
    longitude: float,
    latitude: float,
    radius_km: float,
) -> NearbyResponse:
    if _is_postgresql(session):
        return _nearby_postgresql(session, longitude, latitude, radius_km)

    point = Point(longitude=longitude, latitude=latitude)
    radius_meters = radius_km * 1_000
    farms = [
        _farm_boundary_result(session, boundary, distance_km=_distance_to_boundary_km(boundary.geometry, point))
        for boundary in session.scalars(select(FarmBoundary).order_by(FarmBoundary.id))
    ]
    plots = [
        _plot_boundary_result(session, boundary, distance_km=_distance_to_boundary_km(boundary.geometry, point))
        for boundary in session.scalars(select(PlotBoundary).order_by(PlotBoundary.id))
    ]
    regions = [
        _region_result(region, distance_km=_distance_to_boundary_km(region.geometry, point))
        for region in session.scalars(select(GeoRegion).order_by(GeoRegion.id))
    ]

    return NearbyResponse(
        farms=sorted([item for item in farms if (item.distance_km or 0) * 1_000 <= radius_meters], key=_distance_sort_key),
        plots=sorted([item for item in plots if (item.distance_km or 0) * 1_000 <= radius_meters], key=_distance_sort_key),
        regions=sorted([item for item in regions if (item.distance_km or 0) * 1_000 <= radius_meters], key=_distance_sort_key),
    )


def intersecting_boundaries(
    session: Session,
    relation_type: str | None = None,
) -> IntersectionsResponse:
    if _is_postgresql(session):
        return _intersections_postgresql(session, relation_type)

    intersections: list[IntersectionResult] = []
    farm_boundaries = list(session.scalars(select(FarmBoundary).order_by(FarmBoundary.id)))
    plot_boundaries = list(session.scalars(select(PlotBoundary).order_by(PlotBoundary.id)))

    if relation_type in (None, "farm/farm"):
        for index, first in enumerate(farm_boundaries):
            for second in farm_boundaries[index + 1 :]:
                if boundary_intersects(first.geometry, second.geometry):
                    intersections.append(_intersection_result("farm/farm", "farm", first, "farm", second))

    if relation_type in (None, "farm/plot"):
        for farm_boundary in farm_boundaries:
            for plot_boundary in plot_boundaries:
                if boundary_intersects(farm_boundary.geometry, plot_boundary.geometry):
                    intersections.append(_intersection_result("farm/plot", "farm", farm_boundary, "plot", plot_boundary))

    if relation_type in (None, "plot/plot"):
        for index, first in enumerate(plot_boundaries):
            for second in plot_boundaries[index + 1 :]:
                if boundary_intersects(first.geometry, second.geometry):
                    intersections.append(_intersection_result("plot/plot", "plot", first, "plot", second))

    return IntersectionsResponse(intersections=intersections)


def region_resolver(session: Session, owner_type: BoundaryKind, owner_id: int) -> RegionHierarchyResponse:
    if _is_postgresql(session):
        return _region_resolver_postgresql(session, owner_type, owner_id)

    if owner_type == "farm":
        boundary = session.scalar(select(FarmBoundary).where(FarmBoundary.farm_id == owner_id).order_by(FarmBoundary.id))
        if boundary is None:
            raise LookupError("Farm boundary not found")
        boundary_id = boundary.id
    else:
        boundary = session.scalar(select(PlotBoundary).where(PlotBoundary.plot_id == owner_id).order_by(PlotBoundary.id))
        if boundary is None:
            raise LookupError("Plot boundary not found")
        boundary_id = boundary.id

    centroid = polygon_centroid(boundary.geometry)
    containing_regions = [
        _region_result(region)
        for region in session.scalars(select(GeoRegion).order_by(GeoRegion.id))
        if point_in_polygon(region.geometry, centroid)
    ]
    return RegionHierarchyResponse(
        owner_type=owner_type,
        owner_id=owner_id,
        boundary_id=boundary_id,
        regions=_hierarchy_map(containing_regions),
    )


def bbox_search(
    session: Session,
    west: float,
    south: float,
    east: float,
    north: float,
) -> BBoxSearchResponse:
    if _is_postgresql(session):
        return _bbox_search_postgresql(session, west, south, east, north)

    bbox_polygon = _bbox_polygon(west, south, east, north)
    return BBoxSearchResponse(
        farms=[
            _farm_boundary_result(session, boundary)
            for boundary in session.scalars(select(FarmBoundary).order_by(FarmBoundary.id))
            if boundary_intersects(boundary.geometry, bbox_polygon)
        ],
        plots=[
            _plot_boundary_result(session, boundary)
            for boundary in session.scalars(select(PlotBoundary).order_by(PlotBoundary.id))
            if boundary_intersects(boundary.geometry, bbox_polygon)
        ],
        regions=[
            _region_result(region)
            for region in session.scalars(select(GeoRegion).order_by(GeoRegion.id))
            if boundary_intersects(region.geometry, bbox_polygon)
        ],
    )


def point_in_polygon(boundary: dict[str, Any] | str, point: Point | tuple[float, float]) -> bool:
    point_tuple = (point.longitude, point.latitude) if isinstance(point, Point) else point
    return boundary_contains_point(boundary, point_tuple)


def polygon_centroid(boundary: dict[str, Any] | str) -> Point:
    polygon = parse_geojson_polygon(_load_geometry(boundary))
    ring = polygon["coordinates"][0]
    signed_area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0

    for index in range(len(ring) - 1):
        x1, y1 = ring[index][0], ring[index][1]
        x2, y2 = ring[index + 1][0], ring[index + 1][1]
        cross = x1 * y2 - x2 * y1
        signed_area += cross
        centroid_x += (x1 + x2) * cross
        centroid_y += (y1 + y2) * cross

    signed_area *= 0.5
    if abs(signed_area) < 1e-12:
        longitudes = [position[0] for position in ring[:-1]]
        latitudes = [position[1] for position in ring[:-1]]
        return Point(sum(longitudes) / len(longitudes), sum(latitudes) / len(latitudes))

    return Point(centroid_x / (6 * signed_area), centroid_y / (6 * signed_area))


def polygon_perimeter_meters(boundary: dict[str, Any] | str) -> float:
    polygon = parse_geojson_polygon(_load_geometry(boundary))
    return sum(_ring_perimeter_meters(ring) for ring in polygon["coordinates"])


def compactness_score(boundary: dict[str, Any] | str) -> float:
    polygon = parse_geojson_polygon(_load_geometry(boundary))
    area = calculate_polygon_area(polygon["coordinates"]).square_meters
    perimeter = polygon_perimeter_meters(polygon)
    if perimeter <= 0:
        return 0.0
    return max(min((4 * pi * area) / (perimeter * perimeter), 1.0), 0.0)


def spatial_metrics(boundary: dict[str, Any] | str) -> SpatialMetrics:
    centroid = polygon_centroid(boundary)
    return SpatialMetrics(
        centroid_longitude=centroid.longitude,
        centroid_latitude=centroid.latitude,
        perimeter_meters=polygon_perimeter_meters(boundary),
        compactness_score=compactness_score(boundary),
    )


def _point_lookup_postgresql(session: Session, longitude: float, latitude: float) -> PointLookupResponse:
    return PointLookupResponse(
        farm_boundaries=[
            _farm_boundary_result_from_mapping(row)
            for row in _postgresql_farm_rows(
                session,
                """
                where ST_Contains(fb.geometry, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326))
                order by fb.id
                """,
                {"longitude": longitude, "latitude": latitude},
            )
        ],
        plot_boundaries=[
            _plot_boundary_result_from_mapping(row)
            for row in _postgresql_plot_rows(
                session,
                """
                where ST_Contains(pb.geometry, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326))
                order by pb.id
                """,
                {"longitude": longitude, "latitude": latitude},
            )
        ],
        regions=[
            _region_result_from_mapping(row)
            for row in _postgresql_region_rows(
                session,
                """
                where ST_Contains(gr.geometry, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326))
                order by gr.id
                """,
                {"longitude": longitude, "latitude": latitude},
            )
        ],
    )


def _nearby_postgresql(session: Session, longitude: float, latitude: float, radius_km: float) -> NearbyResponse:
    params = {"longitude": longitude, "latitude": latitude, "radius_meters": radius_km * 1_000}
    point_sql = "ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)"
    return NearbyResponse(
        farms=[
            _farm_boundary_result_from_mapping(row)
            for row in _postgresql_farm_rows(
                session,
                f"""
                where ST_DWithin(fb.geometry::geography, {point_sql}::geography, :radius_meters)
                order by distance_km, fb.id
                """,
                params,
                point_sql=point_sql,
            )
        ],
        plots=[
            _plot_boundary_result_from_mapping(row)
            for row in _postgresql_plot_rows(
                session,
                f"""
                where ST_DWithin(pb.geometry::geography, {point_sql}::geography, :radius_meters)
                order by distance_km, pb.id
                """,
                params,
                point_sql=point_sql,
            )
        ],
        regions=[
            _region_result_from_mapping(row)
            for row in _postgresql_region_rows(
                session,
                f"""
                where ST_DWithin(gr.geometry::geography, {point_sql}::geography, :radius_meters)
                order by distance_km, gr.id
                """,
                params,
                point_sql=point_sql,
            )
        ],
    )


def _intersections_postgresql(session: Session, relation_type: str | None) -> IntersectionsResponse:
    intersections: list[IntersectionResult] = []
    if relation_type in (None, "farm/farm"):
        rows = session.execute(
            text(
                """
                select a.id as first_boundary_id, a.farm_id as first_owner_id,
                    b.id as second_boundary_id, b.farm_id as second_owner_id,
                    a.area_acres as first_area_acres, b.area_acres as second_area_acres,
                    ST_Area(ST_Intersection(a.geometry, b.geometry)::geography) as overlap_area_square_meters
                from farm_boundaries a
                join farm_boundaries b on a.id < b.id and ST_Intersects(a.geometry, b.geometry)
                order by a.id, b.id
                """
            )
        ).mappings()
        intersections.extend(
            _intersection_result_from_mapping("farm/farm", "farm", "farm", row) for row in rows
        )

    if relation_type in (None, "farm/plot"):
        rows = session.execute(
            text(
                """
                select fb.id as first_boundary_id, fb.farm_id as first_owner_id,
                    pb.id as second_boundary_id, pb.plot_id as second_owner_id,
                    fb.area_acres as first_area_acres, pb.area_acres as second_area_acres,
                    ST_Area(ST_Intersection(fb.geometry, pb.geometry)::geography) as overlap_area_square_meters
                from farm_boundaries fb
                join plot_boundaries pb on ST_Intersects(fb.geometry, pb.geometry)
                order by fb.id, pb.id
                """
            )
        ).mappings()
        intersections.extend(
            _intersection_result_from_mapping("farm/plot", "farm", "plot", row) for row in rows
        )

    if relation_type in (None, "plot/plot"):
        rows = session.execute(
            text(
                """
                select a.id as first_boundary_id, a.plot_id as first_owner_id,
                    b.id as second_boundary_id, b.plot_id as second_owner_id,
                    a.area_acres as first_area_acres, b.area_acres as second_area_acres,
                    ST_Area(ST_Intersection(a.geometry, b.geometry)::geography) as overlap_area_square_meters
                from plot_boundaries a
                join plot_boundaries b on a.id < b.id and ST_Intersects(a.geometry, b.geometry)
                order by a.id, b.id
                """
            )
        ).mappings()
        intersections.extend(
            _intersection_result_from_mapping("plot/plot", "plot", "plot", row) for row in rows
        )

    return IntersectionsResponse(intersections=intersections)


def _region_resolver_postgresql(session: Session, owner_type: BoundaryKind, owner_id: int) -> RegionHierarchyResponse:
    if owner_type == "farm":
        row = session.execute(text("select id from farm_boundaries where farm_id = :owner_id order by id limit 1"), {"owner_id": owner_id}).mappings().first()
        not_found = "Farm boundary not found"
        region_sql = """
            select gr.id as region_id, gr.region_type, gr.name, gr.parent_id,
                ST_X(ST_Centroid(gr.geometry)) as centroid_longitude,
                ST_Y(ST_Centroid(gr.geometry)) as centroid_latitude,
                ST_Perimeter(gr.geometry::geography) as perimeter_meters,
                case
                    when ST_Perimeter(gr.geometry::geography) = 0 then 0
                    else LEAST(GREATEST((4 * pi() * ST_Area(gr.geometry::geography))
                        / (ST_Perimeter(gr.geometry::geography) * ST_Perimeter(gr.geometry::geography)), 0), 1)
                end as compactness_score,
                null as distance_km
            from geo_regions gr
            join farm_boundaries fb on fb.id = :boundary_id
            where ST_Contains(gr.geometry, ST_Centroid(fb.geometry))
            order by gr.id
        """
    else:
        row = session.execute(text("select id from plot_boundaries where plot_id = :owner_id order by id limit 1"), {"owner_id": owner_id}).mappings().first()
        not_found = "Plot boundary not found"
        region_sql = """
            select gr.id as region_id, gr.region_type, gr.name, gr.parent_id,
                ST_X(ST_Centroid(gr.geometry)) as centroid_longitude,
                ST_Y(ST_Centroid(gr.geometry)) as centroid_latitude,
                ST_Perimeter(gr.geometry::geography) as perimeter_meters,
                case
                    when ST_Perimeter(gr.geometry::geography) = 0 then 0
                    else LEAST(GREATEST((4 * pi() * ST_Area(gr.geometry::geography))
                        / (ST_Perimeter(gr.geometry::geography) * ST_Perimeter(gr.geometry::geography)), 0), 1)
                end as compactness_score,
                null as distance_km
            from geo_regions gr
            join plot_boundaries pb on pb.id = :boundary_id
            where ST_Contains(gr.geometry, ST_Centroid(pb.geometry))
            order by gr.id
        """

    if row is None:
        raise LookupError(not_found)

    rows = session.execute(text(region_sql), {"boundary_id": row["id"]}).mappings()
    regions = [_region_result_from_mapping(region_row) for region_row in rows]
    return RegionHierarchyResponse(
        owner_type=owner_type,
        owner_id=owner_id,
        boundary_id=row["id"],
        regions=_hierarchy_map(regions),
    )


def _bbox_search_postgresql(
    session: Session,
    west: float,
    south: float,
    east: float,
    north: float,
) -> BBoxSearchResponse:
    envelope_sql = "ST_MakeEnvelope(:west, :south, :east, :north, 4326)"
    params = {"west": west, "south": south, "east": east, "north": north}
    return BBoxSearchResponse(
        farms=[
            _farm_boundary_result_from_mapping(row)
            for row in _postgresql_farm_rows(session, f"where ST_Intersects(fb.geometry, {envelope_sql}) order by fb.id", params)
        ],
        plots=[
            _plot_boundary_result_from_mapping(row)
            for row in _postgresql_plot_rows(session, f"where ST_Intersects(pb.geometry, {envelope_sql}) order by pb.id", params)
        ],
        regions=[
            _region_result_from_mapping(row)
            for row in _postgresql_region_rows(session, f"where ST_Intersects(gr.geometry, {envelope_sql}) order by gr.id", params)
        ],
    )


def _postgresql_farm_rows(
    session: Session,
    where_clause: str,
    params: dict[str, Any],
    point_sql: str | None = None,
) -> list[Any]:
    distance_sql = f"ST_Distance(fb.geometry::geography, {point_sql}::geography) / 1000" if point_sql else "null"
    return list(
        session.execute(
            text(
                f"""
                select fb.id as boundary_id, fb.farm_id as owner_id, f.name as owner_name,
                    fb.area_acres, fb.area_hectares,
                    ST_X(ST_Centroid(fb.geometry)) as centroid_longitude,
                    ST_Y(ST_Centroid(fb.geometry)) as centroid_latitude,
                    ST_Perimeter(fb.geometry::geography) as perimeter_meters,
                    case
                        when ST_Perimeter(fb.geometry::geography) = 0 then 0
                        else LEAST(GREATEST((4 * pi() * ST_Area(fb.geometry::geography))
                            / (ST_Perimeter(fb.geometry::geography) * ST_Perimeter(fb.geometry::geography)), 0), 1)
                    end as compactness_score,
                    {distance_sql} as distance_km
                from farm_boundaries fb
                join farms f on f.id = fb.farm_id
                {where_clause}
                """
            ),
            params,
        ).mappings()
    )


def _postgresql_plot_rows(
    session: Session,
    where_clause: str,
    params: dict[str, Any],
    point_sql: str | None = None,
) -> list[Any]:
    distance_sql = f"ST_Distance(pb.geometry::geography, {point_sql}::geography) / 1000" if point_sql else "null"
    return list(
        session.execute(
            text(
                f"""
                select pb.id as boundary_id, pb.plot_id as owner_id, p.name as owner_name,
                    pb.area_acres, pb.area_hectares,
                    ST_X(ST_Centroid(pb.geometry)) as centroid_longitude,
                    ST_Y(ST_Centroid(pb.geometry)) as centroid_latitude,
                    ST_Perimeter(pb.geometry::geography) as perimeter_meters,
                    case
                        when ST_Perimeter(pb.geometry::geography) = 0 then 0
                        else LEAST(GREATEST((4 * pi() * ST_Area(pb.geometry::geography))
                            / (ST_Perimeter(pb.geometry::geography) * ST_Perimeter(pb.geometry::geography)), 0), 1)
                    end as compactness_score,
                    {distance_sql} as distance_km
                from plot_boundaries pb
                join plots p on p.id = pb.plot_id
                {where_clause}
                """
            ),
            params,
        ).mappings()
    )


def _postgresql_region_rows(
    session: Session,
    where_clause: str,
    params: dict[str, Any],
    point_sql: str | None = None,
) -> list[Any]:
    distance_sql = f"ST_Distance(gr.geometry::geography, {point_sql}::geography) / 1000" if point_sql else "null"
    return list(
        session.execute(
            text(
                f"""
                select gr.id as region_id, gr.region_type, gr.name, gr.parent_id,
                    ST_X(ST_Centroid(gr.geometry)) as centroid_longitude,
                    ST_Y(ST_Centroid(gr.geometry)) as centroid_latitude,
                    ST_Perimeter(gr.geometry::geography) as perimeter_meters,
                    case
                        when ST_Perimeter(gr.geometry::geography) = 0 then 0
                        else LEAST(GREATEST((4 * pi() * ST_Area(gr.geometry::geography))
                            / (ST_Perimeter(gr.geometry::geography) * ST_Perimeter(gr.geometry::geography)), 0), 1)
                    end as compactness_score,
                    {distance_sql} as distance_km
                from geo_regions gr
                {where_clause}
                """
            ),
            params,
        ).mappings()
    )


def _farm_boundary_result(session: Session, boundary: FarmBoundary, distance_km: float | None = None) -> SpatialBoundaryResult:
    farm = session.get(Farm, boundary.farm_id)
    return SpatialBoundaryResult(
        boundary_type="farm",
        boundary_id=boundary.id,
        owner_id=boundary.farm_id,
        owner_name=farm.name if farm else f"Farm #{boundary.farm_id}",
        area_acres=float(boundary.area_acres),
        area_hectares=float(boundary.area_hectares),
        distance_km=distance_km,
        metrics=spatial_metrics(boundary.geometry),
    )


def _plot_boundary_result(session: Session, boundary: PlotBoundary, distance_km: float | None = None) -> SpatialBoundaryResult:
    plot = session.get(Plot, boundary.plot_id)
    return SpatialBoundaryResult(
        boundary_type="plot",
        boundary_id=boundary.id,
        owner_id=boundary.plot_id,
        owner_name=plot.name if plot else f"Plot #{boundary.plot_id}",
        area_acres=float(boundary.area_acres),
        area_hectares=float(boundary.area_hectares),
        distance_km=distance_km,
        metrics=spatial_metrics(boundary.geometry),
    )


def _region_result(region: GeoRegion, distance_km: float | None = None) -> SpatialRegionResult:
    return SpatialRegionResult(
        region_id=region.id,
        region_type=region.region_type,
        name=region.name,
        parent_id=region.parent_id,
        distance_km=distance_km,
        metrics=spatial_metrics(region.geometry),
    )


def _farm_boundary_result_from_mapping(row: Any) -> SpatialBoundaryResult:
    return _boundary_result_from_mapping("farm", row)


def _plot_boundary_result_from_mapping(row: Any) -> SpatialBoundaryResult:
    return _boundary_result_from_mapping("plot", row)


def _boundary_result_from_mapping(boundary_type: BoundaryKind, row: Any) -> SpatialBoundaryResult:
    return SpatialBoundaryResult(
        boundary_type=boundary_type,
        boundary_id=row["boundary_id"],
        owner_id=row["owner_id"],
        owner_name=row["owner_name"],
        area_acres=float(row["area_acres"]),
        area_hectares=float(row["area_hectares"]),
        distance_km=_nullable_float(row["distance_km"]),
        metrics=_metrics_from_mapping(row),
    )


def _region_result_from_mapping(row: Any) -> SpatialRegionResult:
    return SpatialRegionResult(
        region_id=row["region_id"],
        region_type=row["region_type"],
        name=row["name"],
        parent_id=row["parent_id"],
        distance_km=_nullable_float(row["distance_km"]),
        metrics=_metrics_from_mapping(row),
    )


def _metrics_from_mapping(row: Any) -> SpatialMetrics:
    return SpatialMetrics(
        centroid_longitude=float(row["centroid_longitude"]),
        centroid_latitude=float(row["centroid_latitude"]),
        perimeter_meters=float(row["perimeter_meters"]),
        compactness_score=float(row["compactness_score"]),
    )


def _intersection_result(
    relation_type: str,
    first_type: BoundaryKind,
    first: FarmBoundary | PlotBoundary,
    second_type: BoundaryKind,
    second: FarmBoundary | PlotBoundary,
) -> IntersectionResult:
    return IntersectionResult(
        relation_type=relation_type,
        first_boundary_type=first_type,
        first_boundary_id=first.id,
        first_owner_id=first.farm_id if first_type == "farm" else first.plot_id,
        second_boundary_type=second_type,
        second_boundary_id=second.id,
        second_owner_id=second.farm_id if second_type == "farm" else second.plot_id,
        intersects=True,
        first_area_acres=float(first.area_acres),
        second_area_acres=float(second.area_acres),
    )


def _intersection_result_from_mapping(
    relation_type: str,
    first_type: BoundaryKind,
    second_type: BoundaryKind,
    row: Any,
) -> IntersectionResult:
    return IntersectionResult(
        relation_type=relation_type,
        first_boundary_type=first_type,
        first_boundary_id=row["first_boundary_id"],
        first_owner_id=row["first_owner_id"],
        second_boundary_type=second_type,
        second_boundary_id=row["second_boundary_id"],
        second_owner_id=row["second_owner_id"],
        intersects=True,
        first_area_acres=float(row["first_area_acres"]),
        second_area_acres=float(row["second_area_acres"]),
        overlap_area_square_meters=_nullable_float(row["overlap_area_square_meters"]),
    )


def _distance_to_boundary_km(boundary: dict[str, Any] | str, point: Point) -> float:
    if point_in_polygon(boundary, point):
        return 0.0
    centroid = polygon_centroid(boundary)
    return _haversine_meters(point, centroid) / 1_000


def _distance_sort_key(item: SpatialBoundaryResult | SpatialRegionResult) -> float:
    return item.distance_km if item.distance_km is not None else 0.0


def _hierarchy_map(regions: list[SpatialRegionResult]) -> dict[str, SpatialRegionResult | None]:
    by_type = {region.region_type: region for region in regions}
    return {region_type: by_type.get(region_type) for region_type in REGION_ORDER}


def _bbox_polygon(west: float, south: float, east: float, north: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
    }


def _load_geometry(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(value)


def _ring_perimeter_meters(ring: list[list[float]]) -> float:
    return sum(
        _haversine_meters(
            Point(longitude=ring[index][0], latitude=ring[index][1]),
            Point(longitude=ring[index + 1][0], latitude=ring[index + 1][1]),
        )
        for index in range(len(ring) - 1)
    )


def _haversine_meters(first: Point, second: Point) -> float:
    first_latitude = radians(first.latitude)
    second_latitude = radians(second.latitude)
    delta_latitude = radians(second.latitude - first.latitude)
    delta_longitude = radians(second.longitude - first.longitude)
    value = (
        sin(delta_latitude / 2) * sin(delta_latitude / 2)
        + cos(first_latitude) * cos(second_latitude) * sin(delta_longitude / 2) * sin(delta_longitude / 2)
    )
    return EARTH_RADIUS_METERS * 2 * atan2(sqrt(value), sqrt(1 - value))


def _nullable_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _is_postgresql(session: Session) -> bool:
    return session.get_bind().dialect.name == "postgresql"
