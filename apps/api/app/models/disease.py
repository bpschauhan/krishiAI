from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Crop(Base):
    __tablename__ = "crops"
    __table_args__ = (UniqueConstraint("name", name="uq_crops_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    scientific_name: Mapped[str | None] = mapped_column(String(180), nullable=True)

    diseases = relationship("CropDisease", back_populates="crop", cascade="all, delete-orphan")
    stages = relationship("CropStage", back_populates="crop", cascade="all, delete-orphan")


class CropDisease(Base):
    __tablename__ = "crop_diseases"
    __table_args__ = (UniqueConstraint("crop_id", "name", name="uq_crop_diseases_crop_id_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    severity_scale: Mapped[int] = mapped_column(nullable=False, default=100)

    crop = relationship("Crop", back_populates="diseases")


class CropStage(Base):
    __tablename__ = "crop_stages"
    __table_args__ = (UniqueConstraint("crop_id", "name", name="uq_crop_stages_crop_id_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    crop = relationship("Crop", back_populates="stages")


class DiseaseRiskAssessment(Base):
    __tablename__ = "disease_risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    crop_stage_id: Mapped[int] = mapped_column(ForeignKey("crop_stages.id"), nullable=False, index=True)
    disease_id: Mapped[int] = mapped_column(ForeignKey("crop_diseases.id"), nullable=False, index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    level: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    crop = relationship("Crop")
    crop_stage = relationship("CropStage")
    disease = relationship("CropDisease")
