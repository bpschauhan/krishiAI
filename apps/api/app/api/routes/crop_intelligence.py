from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.crop_intelligence import CropCalendarRead, CropSeasonRead, CropSuitabilityResponse
from app.services.crop_intelligence import CropIntelligenceService, crop_intelligence_service

router = APIRouter()


def get_crop_intelligence_service() -> CropIntelligenceService:
    return crop_intelligence_service


@router.get("/crop-seasons", response_model=list[CropSeasonRead])
def get_crop_seasons(
    db: Session = Depends(get_db),
    service: CropIntelligenceService = Depends(get_crop_intelligence_service),
) -> list[CropSeasonRead]:
    return service.list_seasons(db)


@router.get("/crop-calendar", response_model=list[CropCalendarRead])
def get_crop_calendar(
    district_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    service: CropIntelligenceService = Depends(get_crop_intelligence_service),
) -> list[CropCalendarRead]:
    try:
        return service.list_calendar(db, district_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/crop-suitability", response_model=CropSuitabilityResponse)
def get_crop_suitability(
    farm_id: int = Query(gt=0),
    crop_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    service: CropIntelligenceService = Depends(get_crop_intelligence_service),
) -> CropSuitabilityResponse:
    try:
        return service.assess_suitability(db, farm_id=farm_id, crop_id=crop_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
