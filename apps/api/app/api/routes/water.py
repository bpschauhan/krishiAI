from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.water import WaterIntelligenceResponse
from app.services.water_intelligence import WaterIntelligenceService, water_intelligence_service

router = APIRouter()


def get_water_intelligence_service() -> WaterIntelligenceService:
    return water_intelligence_service


@router.get("/water-intelligence", response_model=WaterIntelligenceResponse)
def get_water_intelligence(
    farm_id: int = Query(gt=0),
    crop_id: int = Query(gt=0),
    crop_stage_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    service: WaterIntelligenceService = Depends(get_water_intelligence_service),
) -> WaterIntelligenceResponse:
    try:
        return service.assess_farm(db, farm_id=farm_id, crop_id=crop_id, crop_stage_id=crop_stage_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
