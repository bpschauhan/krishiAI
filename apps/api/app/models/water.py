from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropWaterProfile(Base):
    __tablename__ = "crop_water_profiles"
    __table_args__ = (UniqueConstraint("crop_id", "stage_id", name="uq_crop_water_profiles_crop_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("crop_stages.id"), nullable=False, index=True)
    min_mm_per_day: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    optimal_mm_per_day: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    max_mm_per_day: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    crop = relationship("Crop")
    stage = relationship("CropStage")


class FarmWaterRequirement(Base):
    __tablename__ = "farm_water_requirements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("crop_stages.id"), nullable=False, index=True)
    estimated_requirement_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    rainfall_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    deficit_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    surplus_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    crop = relationship("Crop")
    stage = relationship("CropStage")


class WaterAssessmentHistory(Base):
    __tablename__ = "water_assessment_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("crop_stages.id"), nullable=False, index=True)
    estimated_requirement_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    rainfall_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    deficit_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    surplus_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    crop = relationship("Crop")
    stage = relationship("CropStage")
