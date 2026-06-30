from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from app.db.session import Base


class PostGISGeometry(UserDefinedType):
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **_: object) -> str:
        return f"geometry({self.geometry_type},{self.srid})"


@compiles(PostGISGeometry, "sqlite")
def _compile_sqlite_geometry(_: PostGISGeometry, __: object, **___: object) -> str:
    return "TEXT"


class FarmBoundary(Base):
    __tablename__ = "farm_boundaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    geometry: Mapped[str] = mapped_column(PostGISGeometry("POLYGON"), nullable=False)
    area_square_meters: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    area_hectares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    area_acres: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PlotBoundary(Base):
    __tablename__ = "plot_boundaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plot_id: Mapped[int] = mapped_column(ForeignKey("plots.id"), nullable=False, index=True)
    geometry: Mapped[str] = mapped_column(PostGISGeometry("POLYGON"), nullable=False)
    area_square_meters: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    area_hectares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    area_acres: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class GeoRegion(Base):
    __tablename__ = "geo_regions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    region_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("geo_regions.id"), nullable=True, index=True)
    geometry: Mapped[str] = mapped_column(PostGISGeometry("GEOMETRY"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    parent = relationship("GeoRegion", remote_side=[id])
