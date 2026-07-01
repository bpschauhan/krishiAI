from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.spatial import (
    BBoxSearchRequest,
    BBoxSearchResponse,
    IntersectionKind,
    IntersectionsResponse,
    NearbyRequest,
    NearbyResponse,
    PointLookupRequest,
    PointLookupResponse,
    RegionHierarchyResponse,
)
from app.services.spatial_intelligence import (
    bbox_search,
    intersecting_boundaries,
    nearest_boundaries,
    point_lookup,
    region_resolver,
)

router = APIRouter(prefix="/spatial")


@router.post("/point-lookup", response_model=PointLookupResponse)
def lookup_point(payload: PointLookupRequest, db: Session = Depends(get_db)) -> PointLookupResponse:
    return point_lookup(db, payload.longitude, payload.latitude)


@router.post("/nearby", response_model=NearbyResponse)
def nearby_search(payload: NearbyRequest, db: Session = Depends(get_db)) -> NearbyResponse:
    return nearest_boundaries(db, payload.longitude, payload.latitude, payload.radius_km)


@router.get("/intersections", response_model=IntersectionsResponse)
def boundary_intersections(
    relation_type: IntersectionKind | None = Query(default=None),
    db: Session = Depends(get_db),
) -> IntersectionsResponse:
    return intersecting_boundaries(db, relation_type)


@router.get("/farm/{farm_id}/regions", response_model=RegionHierarchyResponse)
def farm_regions(farm_id: int, db: Session = Depends(get_db)) -> RegionHierarchyResponse:
    try:
        return region_resolver(db, "farm", farm_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/plot/{plot_id}/regions", response_model=RegionHierarchyResponse)
def plot_regions(plot_id: int, db: Session = Depends(get_db)) -> RegionHierarchyResponse:
    try:
        return region_resolver(db, "plot", plot_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/bbox-search", response_model=BBoxSearchResponse)
def bounding_box_search(payload: BBoxSearchRequest, db: Session = Depends(get_db)) -> BBoxSearchResponse:
    return bbox_search(db, payload.west, payload.south, payload.east, payload.north)
