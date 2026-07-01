from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropSeason(Base):
    __tablename__ = "crop_seasons"
    __table_args__ = (UniqueConstraint("crop_id", "season_type", name="uq_crop_seasons_crop_season_type"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    season_name: Mapped[str] = mapped_column(String(120), nullable=False)
    season_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)

    crop = relationship("Crop")


class CropCalendar(Base):
    __tablename__ = "crop_calendars"
    __table_args__ = (UniqueConstraint("crop_id", "district_id", name="uq_crop_calendars_crop_district"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), nullable=False, index=True)
    sowing_start: Mapped[date] = mapped_column(Date, nullable=False)
    sowing_end: Mapped[date] = mapped_column(Date, nullable=False)
    harvest_start: Mapped[date] = mapped_column(Date, nullable=False)
    harvest_end: Mapped[date] = mapped_column(Date, nullable=False)

    crop = relationship("Crop")
    district = relationship("District")


class CropSuitabilityProfile(Base):
    __tablename__ = "crop_suitability_profiles"
    __table_args__ = (UniqueConstraint("crop_id", name="uq_crop_suitability_profiles_crop"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    min_temperature: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_temperature: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    min_rainfall: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    max_rainfall: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    preferred_soil_type: Mapped[str | None] = mapped_column(String(120), nullable=True)

    crop = relationship("Crop")


class CropSuitabilityAssessment(Base):
    __tablename__ = "crop_suitability_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"), nullable=False, index=True)
    suitability_score: Mapped[int] = mapped_column(nullable=False)
    season: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    crop = relationship("Crop")
