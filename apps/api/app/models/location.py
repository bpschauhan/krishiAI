from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("name", "state", name="uq_district_name_state"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(80), nullable=False, default="Uttar Pradesh")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farmers = relationship("Farmer", back_populates="district")
    farms = relationship("Farm", back_populates="district")
