"""create geospatial core tables

Revision ID: 202606300001
Revises: 202606260001
Create Date: 2026-06-30 21:22:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import UserDefinedType

revision: str = "202606300001"
down_revision: str | None = "202606260001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class Geometry(UserDefinedType):
    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **_: object) -> str:
        return f"geometry({self.geometry_type},{self.srid})"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "farm_boundaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("geometry", Geometry("POLYGON"), nullable=False),
        sa.Column("area_square_meters", sa.Numeric(14, 2), nullable=False),
        sa.Column("area_hectares", sa.Numeric(12, 4), nullable=False),
        sa.Column("area_acres", sa.Numeric(12, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farm_boundaries_id"), "farm_boundaries", ["id"], unique=False)
    op.create_index(op.f("ix_farm_boundaries_farm_id"), "farm_boundaries", ["farm_id"], unique=False)
    op.create_index("ix_farm_boundaries_geometry", "farm_boundaries", ["geometry"], postgresql_using="gist")

    op.create_table(
        "plot_boundaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plot_id", sa.Integer(), nullable=False),
        sa.Column("geometry", Geometry("POLYGON"), nullable=False),
        sa.Column("area_square_meters", sa.Numeric(14, 2), nullable=False),
        sa.Column("area_hectares", sa.Numeric(12, 4), nullable=False),
        sa.Column("area_acres", sa.Numeric(12, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plot_id"], ["plots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plot_boundaries_id"), "plot_boundaries", ["id"], unique=False)
    op.create_index(op.f("ix_plot_boundaries_plot_id"), "plot_boundaries", ["plot_id"], unique=False)
    op.create_index("ix_plot_boundaries_geometry", "plot_boundaries", ["geometry"], postgresql_using="gist")

    op.create_table(
        "geo_regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_type", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("geometry", Geometry("GEOMETRY"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["geo_regions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_geo_regions_id"), "geo_regions", ["id"], unique=False)
    op.create_index(op.f("ix_geo_regions_name"), "geo_regions", ["name"], unique=False)
    op.create_index(op.f("ix_geo_regions_parent_id"), "geo_regions", ["parent_id"], unique=False)
    op.create_index(op.f("ix_geo_regions_region_type"), "geo_regions", ["region_type"], unique=False)
    op.create_index("ix_geo_regions_geometry", "geo_regions", ["geometry"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("ix_geo_regions_geometry", table_name="geo_regions", postgresql_using="gist")
    op.drop_index(op.f("ix_geo_regions_region_type"), table_name="geo_regions")
    op.drop_index(op.f("ix_geo_regions_parent_id"), table_name="geo_regions")
    op.drop_index(op.f("ix_geo_regions_name"), table_name="geo_regions")
    op.drop_index(op.f("ix_geo_regions_id"), table_name="geo_regions")
    op.drop_table("geo_regions")

    op.drop_index("ix_plot_boundaries_geometry", table_name="plot_boundaries", postgresql_using="gist")
    op.drop_index(op.f("ix_plot_boundaries_plot_id"), table_name="plot_boundaries")
    op.drop_index(op.f("ix_plot_boundaries_id"), table_name="plot_boundaries")
    op.drop_table("plot_boundaries")

    op.drop_index("ix_farm_boundaries_geometry", table_name="farm_boundaries", postgresql_using="gist")
    op.drop_index(op.f("ix_farm_boundaries_farm_id"), table_name="farm_boundaries")
    op.drop_index(op.f("ix_farm_boundaries_id"), table_name="farm_boundaries")
    op.drop_table("farm_boundaries")
