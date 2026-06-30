from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians
from typing import Any, Literal

EARTH_RADIUS_METERS = 6_371_008.8
SQUARE_METERS_PER_HECTARE = 10_000
SQUARE_METERS_PER_ACRE = 4_046.8564224

GeoJSONType = Literal["Polygon", "Feature", "FeatureCollection"]


class GeoJSONValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AreaMeasurement:
    square_meters: float
    hectares: float
    acres: float


def parse_geojson_polygon(payload: dict[str, Any]) -> dict[str, Any]:
    geojson_type = payload.get("type")
    if geojson_type == "Polygon":
        polygon = payload
    elif geojson_type == "Feature":
        geometry = payload.get("geometry")
        if not isinstance(geometry, dict):
            raise GeoJSONValidationError("Feature must include a geometry object")
        if geometry.get("type") != "Polygon":
            raise GeoJSONValidationError("Feature geometry must be a Polygon")
        polygon = geometry
    elif geojson_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or len(features) != 1:
            raise GeoJSONValidationError("FeatureCollection must contain exactly one Polygon feature")
        feature = features[0]
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise GeoJSONValidationError("FeatureCollection entries must be GeoJSON Features")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
            raise GeoJSONValidationError("FeatureCollection feature geometry must be a Polygon")
        polygon = geometry
    else:
        raise GeoJSONValidationError("GeoJSON payload must be a Polygon, Feature, or FeatureCollection")

    validate_polygon_coordinates(polygon.get("coordinates"))
    return {"type": "Polygon", "coordinates": polygon["coordinates"]}


def validate_polygon_coordinates(coordinates: Any) -> None:
    if not isinstance(coordinates, list) or not coordinates:
        raise GeoJSONValidationError("Polygon coordinates must include at least one linear ring")

    for ring in coordinates:
        _validate_linear_ring(ring)


def calculate_polygon_area(coordinates: list[list[list[float]]]) -> AreaMeasurement:
    if not coordinates:
        raise GeoJSONValidationError("Polygon coordinates are required")

    outer_area = abs(_ring_area_square_meters(coordinates[0]))
    holes_area = sum(abs(_ring_area_square_meters(ring)) for ring in coordinates[1:])
    square_meters = max(outer_area - holes_area, 0)

    return AreaMeasurement(
        square_meters=square_meters,
        hectares=square_meters / SQUARE_METERS_PER_HECTARE,
        acres=square_meters / SQUARE_METERS_PER_ACRE,
    )


def _validate_linear_ring(ring: Any) -> None:
    if not isinstance(ring, list) or len(ring) < 4:
        raise GeoJSONValidationError("A Polygon linear ring must contain at least four positions")

    for position in ring:
        _validate_position(position)

    if ring[0][:2] != ring[-1][:2]:
        raise GeoJSONValidationError("A Polygon linear ring must be closed")


def _validate_position(position: Any) -> None:
    if not isinstance(position, list) or len(position) < 2:
        raise GeoJSONValidationError("Each position must include longitude and latitude")
    longitude, latitude = position[0], position[1]
    if not isinstance(longitude, int | float) or not isinstance(latitude, int | float):
        raise GeoJSONValidationError("Coordinates must be numeric")
    if longitude < -180 or longitude > 180:
        raise GeoJSONValidationError("Longitude must be between -180 and 180")
    if latitude < -90 or latitude > 90:
        raise GeoJSONValidationError("Latitude must be between -90 and 90")


def _ring_area_square_meters(ring: list[list[float]]) -> float:
    reference_latitude = sum(position[1] for position in ring[:-1]) / (len(ring) - 1)
    projected_points = [
        (
            radians(position[0]) * EARTH_RADIUS_METERS * cos(radians(reference_latitude)),
            radians(position[1]) * EARTH_RADIUS_METERS,
        )
        for position in ring
    ]

    area = 0.0
    for index in range(len(projected_points) - 1):
        x1, y1 = projected_points[index]
        x2, y2 = projected_points[index + 1]
        area += x1 * y2 - x2 * y1
    return area / 2
