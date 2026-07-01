from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.disease import DiseaseRiskResponse
from app.services.disease_risk import DiseaseRiskService, disease_risk_service

router = APIRouter()


def get_disease_risk_service() -> DiseaseRiskService:
    return disease_risk_service


@router.get("/disease-risk", response_model=DiseaseRiskResponse)
def get_disease_risk(
    farm_id: int = Query(gt=0),
    crop_id: int = Query(gt=0),
    crop_stage_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    service: DiseaseRiskService = Depends(get_disease_risk_service),
) -> DiseaseRiskResponse:
    try:
        return service.assess_farm(db, farm_id=farm_id, crop_id=crop_id, crop_stage_id=crop_stage_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
