from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    village: Mapped[str] = mapped_column(String(160), nullable=False)
    total_acreage: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    farmer = relationship("Farmer", back_populates="farms")
    district = relationship("District", back_populates="farms")
    plots = relationship("Plot", back_populates="farm", cascade="all, delete-orphan")
