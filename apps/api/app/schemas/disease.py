from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["Low", "Medium", "High"]


class DiseaseRiskResult(BaseModel):
    disease_id: int
    disease_name: str
    risk_score: int
    risk_level: RiskLevel
    contributing_factors: list[str]


class DiseaseRiskResponse(BaseModel):
    farm_id: int
    crop_id: int
    crop_name: str
    crop_stage_id: int
    crop_stage_name: str
    risk_score: int
    risk_level: RiskLevel
    disease_results: list[DiseaseRiskResult]
    assessed_at: datetime


class DiseaseRiskAssessmentRead(BaseModel):
    id: int
    farm_id: int
    crop_id: int
    crop_stage_id: int
    disease_id: int
    score: float
    level: RiskLevel
    assessed_at: datetime
