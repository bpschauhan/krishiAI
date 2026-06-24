from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    village: Mapped[str] = mapped_column(String(160), nullable=False)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), nullable=False)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), nullable=False)

    district = relationship("District", back_populates="farmers")
    language = relationship("Language", back_populates="farmers")
    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
