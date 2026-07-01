"""create crop intelligence tables

Revision ID: 202607010004
Revises: 202607010003
Create Date: 2026-07-01 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607010004"
down_revision: str | None = "202607010003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crop_seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("season_name", sa.String(length=120), nullable=False),
        sa.Column("season_type", sa.String(length=24), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "season_type", name="uq_crop_seasons_crop_season_type"),
    )
    op.create_index(op.f("ix_crop_seasons_id"), "crop_seasons", ["id"], unique=False)
    op.create_index(op.f("ix_crop_seasons_crop_id"), "crop_seasons", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_seasons_season_type"), "crop_seasons", ["season_type"], unique=False)

    op.create_table(
        "crop_calendars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("sowing_start", sa.Date(), nullable=False),
        sa.Column("sowing_end", sa.Date(), nullable=False),
        sa.Column("harvest_start", sa.Date(), nullable=False),
        sa.Column("harvest_end", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "district_id", name="uq_crop_calendars_crop_district"),
    )
    op.create_index(op.f("ix_crop_calendars_id"), "crop_calendars", ["id"], unique=False)
    op.create_index(op.f("ix_crop_calendars_crop_id"), "crop_calendars", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_calendars_district_id"), "crop_calendars", ["district_id"], unique=False)

    op.create_table(
        "crop_suitability_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("min_temperature", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_temperature", sa.Numeric(5, 2), nullable=False),
        sa.Column("min_rainfall", sa.Numeric(8, 2), nullable=False),
        sa.Column("max_rainfall", sa.Numeric(8, 2), nullable=False),
        sa.Column("preferred_soil_type", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", name="uq_crop_suitability_profiles_crop"),
    )
    op.create_index(op.f("ix_crop_suitability_profiles_id"), "crop_suitability_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_crop_suitability_profiles_crop_id"), "crop_suitability_profiles", ["crop_id"], unique=False)

    op.create_table(
        "crop_suitability_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("suitability_score", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crop_suitability_assessments_id"), "crop_suitability_assessments", ["id"], unique=False)
    op.create_index(op.f("ix_crop_suitability_assessments_farm_id"), "crop_suitability_assessments", ["farm_id"], unique=False)
    op.create_index(op.f("ix_crop_suitability_assessments_crop_id"), "crop_suitability_assessments", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_suitability_assessments_season"), "crop_suitability_assessments", ["season"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_crop_suitability_assessments_season"), table_name="crop_suitability_assessments")
    op.drop_index(op.f("ix_crop_suitability_assessments_crop_id"), table_name="crop_suitability_assessments")
    op.drop_index(op.f("ix_crop_suitability_assessments_farm_id"), table_name="crop_suitability_assessments")
    op.drop_index(op.f("ix_crop_suitability_assessments_id"), table_name="crop_suitability_assessments")
    op.drop_table("crop_suitability_assessments")

    op.drop_index(op.f("ix_crop_suitability_profiles_crop_id"), table_name="crop_suitability_profiles")
    op.drop_index(op.f("ix_crop_suitability_profiles_id"), table_name="crop_suitability_profiles")
    op.drop_table("crop_suitability_profiles")

    op.drop_index(op.f("ix_crop_calendars_district_id"), table_name="crop_calendars")
    op.drop_index(op.f("ix_crop_calendars_crop_id"), table_name="crop_calendars")
    op.drop_index(op.f("ix_crop_calendars_id"), table_name="crop_calendars")
    op.drop_table("crop_calendars")

    op.drop_index(op.f("ix_crop_seasons_season_type"), table_name="crop_seasons")
    op.drop_index(op.f("ix_crop_seasons_crop_id"), table_name="crop_seasons")
    op.drop_index(op.f("ix_crop_seasons_id"), table_name="crop_seasons")
    op.drop_table("crop_seasons")
