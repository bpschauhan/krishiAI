from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.geospatial import GeoRegion
from app.utils.geo import GeoJSONValidationError, parse_geojson_polygon

Point = tuple[float, float]
BBox = tuple[float, float, float, float]


def boundary_contains_point(boundary: dict[str, Any] | str, point: Point | dict[str, Any]) -> bool:
    polygon = parse_geojson_polygon(_load_geometry(boundary))
    longitude, latitude = _parse_point(point)
    coordinates = polygon["coordinates"]
    if not _point_in_ring((longitude, latitude), coordinates[0]):
        return False
    return not any(_point_in_ring((longitude, latitude), ring) for ring in coordinates[1:])


def boundary_intersects(first_boundary: dict[str, Any] | str, second_boundary: dict[str, Any] | str) -> bool:
    first = parse_geojson_polygon(_load_geometry(first_boundary))
    second = parse_geojson_polygon(_load_geometry(second_boundary))
    if not _bboxes_intersect(boundary_bbox(first), boundary_bbox(second)):
        return False

    first_segments = _polygon_segments(first["coordinates"])
    second_segments = _polygon_segments(second["coordinates"])
    if any(_segments_intersect(a1, a2, b1, b2) for a1, a2 in first_segments for b1, b2 in second_segments):
        return True

    first_point = tuple(first["coordinates"][0][0][:2])
    second_point = tuple(second["coordinates"][0][0][:2])
    return boundary_contains_point(first, second_point) or boundary_contains_point(second, first_point)


def boundary_bbox(boundary: dict[str, Any] | str) -> BBox:
    polygon = parse_geojson_polygon(_load_geometry(boundary))
    positions = [position for ring in polygon["coordinates"] for position in ring]
    longitudes = [position[0] for position in positions]
    latitudes = [position[1] for position in positions]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def region_lookup(
    session: Session,
    point: Point | dict[str, Any],
    region_type: str | None = None,
) -> list[GeoRegion]:
    longitude, latitude = _parse_point(point)

    if session.get_bind().dialect.name == "postgresql":
        clauses = ["ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326))"]
        params: dict[str, Any] = {"longitude": longitude, "latitude": latitude}
        if region_type:
            clauses.append("region_type = :region_type")
            params["region_type"] = region_type
        rows = session.execute(
            text(f"select id from geo_regions where {' and '.join(clauses)} order by id"),
            params,
        )
        region_ids = [row[0] for row in rows]
        if not region_ids:
            return []
        return list(session.scalars(select(GeoRegion).where(GeoRegion.id.in_(region_ids)).order_by(GeoRegion.id)))

    statement = select(GeoRegion).order_by(GeoRegion.id)
    if region_type:
        statement = statement.where(GeoRegion.region_type == region_type)
    return [
        region
        for region in session.scalars(statement)
        if boundary_contains_point(region.geometry, (longitude, latitude))
    ]


def _load_geometry(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return json.loads(value)


def _parse_point(point: Point | dict[str, Any]) -> Point:
    if isinstance(point, dict):
        if point.get("type") != "Point":
            raise GeoJSONValidationError("Point geometry must have type Point")
        coordinates = point.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise GeoJSONValidationError("Point coordinates must include longitude and latitude")
        longitude, latitude = coordinates[0], coordinates[1]
    else:
        longitude, latitude = point

    if not isinstance(longitude, int | float) or not isinstance(latitude, int | float):
        raise GeoJSONValidationError("Point coordinates must be numeric")
    if longitude < -180 or longitude > 180:
        raise GeoJSONValidationError("Longitude must be between -180 and 180")
    if latitude < -90 or latitude > 90:
        raise GeoJSONValidationError("Latitude must be between -90 and 90")
    return float(longitude), float(latitude)


def _point_in_ring(point: Point, ring: list[list[float]]) -> bool:
    longitude, latitude = point
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[0], previous[1]
        x2, y2 = current[0], current[1]
        crosses = (y1 > latitude) != (y2 > latitude)
        if crosses:
            intersection_longitude = (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
            if longitude < intersection_longitude:
                inside = not inside
        previous = current
    return inside


def _polygon_segments(coordinates: list[list[list[float]]]) -> list[tuple[Point, Point]]:
    segments: list[tuple[Point, Point]] = []
    for ring in coordinates:
        for index in range(len(ring) - 1):
            segments.append((tuple(ring[index][:2]), tuple(ring[index + 1][:2])))
    return segments


def _segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    orientation_a = _orientation(a1, a2, b1)
    orientation_b = _orientation(a1, a2, b2)
    orientation_c = _orientation(b1, b2, a1)
    orientation_d = _orientation(b1, b2, a2)

    if orientation_a == 0 and _on_segment(a1, b1, a2):
        return True
    if orientation_b == 0 and _on_segment(a1, b2, a2):
        return True
    if orientation_c == 0 and _on_segment(b1, a1, b2):
        return True
    if orientation_d == 0 and _on_segment(b1, a2, b2):
        return True
    return orientation_a != orientation_b and orientation_c != orientation_d


def _orientation(a: Point, b: Point, c: Point) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) < 1e-12:
        return 0
    return 1 if value > 0 else 2


def _on_segment(a: Point, b: Point, c: Point) -> bool:
    return (
        min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
        and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])
    )


def _bboxes_intersect(first: BBox, second: BBox) -> bool:
    return not (
        first[2] < second[0]
        or second[2] < first[0]
        or first[3] < second[1]
        or second[3] < first[1]
    )
