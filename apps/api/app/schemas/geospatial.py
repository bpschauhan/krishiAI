from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.geo import GeoJSONValidationError, parse_geojson_polygon


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: list[Any]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: dict[str, Any] | None = None


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]


GeoJSONInput = dict[str, Any]


class FarmBoundaryCreate(BaseModel):
    farm_id: int = Field(gt=0)
    geometry: GeoJSONInput

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: GeoJSONInput) -> GeoJSONInput:
        try:
            return parse_geojson_polygon(value)
        except GeoJSONValidationError as exc:
            raise ValueError(str(exc)) from exc


class FarmBoundaryUpdate(BaseModel):
    geometry: GeoJSONInput

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: GeoJSONInput) -> GeoJSONInput:
        try:
            return parse_geojson_polygon(value)
        except GeoJSONValidationError as exc:
            raise ValueError(str(exc)) from exc


class FarmBoundaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    geometry: GeoJSONInput
    area_square_meters: Decimal
    area_hectares: Decimal
    area_acres: Decimal
    created_at: datetime
    updated_at: datetime


class PlotBoundaryCreate(BaseModel):
    plot_id: int = Field(gt=0)
    geometry: GeoJSONInput

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: GeoJSONInput) -> GeoJSONInput:
        try:
            return parse_geojson_polygon(value)
        except GeoJSONValidationError as exc:
            raise ValueError(str(exc)) from exc


class PlotBoundaryUpdate(BaseModel):
    geometry: GeoJSONInput

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: GeoJSONInput) -> GeoJSONInput:
        try:
            return parse_geojson_polygon(value)
        except GeoJSONValidationError as exc:
            raise ValueError(str(exc)) from exc


class PlotBoundaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plot_id: int
    geometry: GeoJSONInput
    area_square_meters: Decimal
    area_hectares: Decimal
    area_acres: Decimal
    created_at: datetime
    updated_at: datetime


class GeoRegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region_type: str
    name: str
    parent_id: int | None = None
    geometry: GeoJSONInput
    created_at: datetime
    updated_at: datetime
