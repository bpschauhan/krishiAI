from typing import Literal

from pydantic import BaseModel, Field, model_validator


BoundaryKind = Literal["farm", "plot"]
RegionType = Literal["country", "state", "district", "block", "village"]
IntersectionKind = Literal["farm/farm", "farm/plot", "plot/plot"]


class PointLookupRequest(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class NearbyRequest(PointLookupRequest):
    radius_km: float = Field(gt=0, le=500)


class BBoxSearchRequest(BaseModel):
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def validate_bbox(self) -> "BBoxSearchRequest":
        if self.west >= self.east:
            raise ValueError("west must be less than east")
        if self.south >= self.north:
            raise ValueError("south must be less than north")
        return self


class SpatialMetrics(BaseModel):
    centroid_longitude: float
    centroid_latitude: float
    perimeter_meters: float
    compactness_score: float


class SpatialBoundaryResult(BaseModel):
    boundary_type: BoundaryKind
    boundary_id: int
    owner_id: int
    owner_name: str
    area_acres: float
    area_hectares: float
    distance_km: float | None = None
    metrics: SpatialMetrics


class SpatialRegionResult(BaseModel):
    region_id: int
    region_type: str
    name: str
    parent_id: int | None = None
    distance_km: float | None = None
    metrics: SpatialMetrics


class PointLookupResponse(BaseModel):
    farm_boundaries: list[SpatialBoundaryResult]
    plot_boundaries: list[SpatialBoundaryResult]
    regions: list[SpatialRegionResult]


class NearbyResponse(BaseModel):
    farms: list[SpatialBoundaryResult]
    plots: list[SpatialBoundaryResult]
    regions: list[SpatialRegionResult]


class IntersectionResult(BaseModel):
    relation_type: IntersectionKind
    first_boundary_type: BoundaryKind
    first_boundary_id: int
    first_owner_id: int
    second_boundary_type: BoundaryKind
    second_boundary_id: int
    second_owner_id: int
    intersects: bool
    first_area_acres: float
    second_area_acres: float
    overlap_area_square_meters: float | None = None


class IntersectionsResponse(BaseModel):
    intersections: list[IntersectionResult]


class RegionHierarchyResponse(BaseModel):
    owner_type: BoundaryKind
    owner_id: int
    boundary_id: int
    regions: dict[RegionType, SpatialRegionResult | None]


class BBoxSearchResponse(BaseModel):
    farms: list[SpatialBoundaryResult]
    plots: list[SpatialBoundaryResult]
    regions: list[SpatialRegionResult]
