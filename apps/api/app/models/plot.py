from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    acreage: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_crop: Mapped[str | None] = mapped_column(String(120), nullable=True)

    farm = relationship("Farm", back_populates="plots")
