from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

WaterStatus = Literal["Adequate", "Deficit", "Surplus"]


class WaterIntelligenceResponse(BaseModel):
    farm_id: int
    crop_id: int
    crop_name: str
    crop_stage_id: int
    crop_stage_name: str
    estimated_requirement_mm: Decimal
    rainfall_mm: Decimal
    deficit_mm: Decimal
    surplus_mm: Decimal
    status: WaterStatus
    calculated_at: datetime


class WaterAssessmentHistoryRead(BaseModel):
    id: int
    farm_id: int
    crop_id: int
    stage_id: int
    estimated_requirement_mm: Decimal
    rainfall_mm: Decimal
    deficit_mm: Decimal
    surplus_mm: Decimal
    status: WaterStatus
    assessed_at: datetime
