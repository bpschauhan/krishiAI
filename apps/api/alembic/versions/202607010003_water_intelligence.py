"""create water intelligence tables

Revision ID: 202607010003
Revises: 202607010002
Create Date: 2026-07-01 11:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607010003"
down_revision: str | None = "202607010002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crop_water_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("min_mm_per_day", sa.Numeric(6, 2), nullable=False),
        sa.Column("optimal_mm_per_day", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_mm_per_day", sa.Numeric(6, 2), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["crop_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "stage_id", name="uq_crop_water_profiles_crop_stage"),
    )
    op.create_index(op.f("ix_crop_water_profiles_id"), "crop_water_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_crop_water_profiles_crop_id"), "crop_water_profiles", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_water_profiles_stage_id"), "crop_water_profiles", ["stage_id"], unique=False)

    op.create_table(
        "farm_water_requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("estimated_requirement_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("deficit_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("surplus_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["crop_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farm_water_requirements_id"), "farm_water_requirements", ["id"], unique=False)
    op.create_index(op.f("ix_farm_water_requirements_farm_id"), "farm_water_requirements", ["farm_id"], unique=False)
    op.create_index(op.f("ix_farm_water_requirements_crop_id"), "farm_water_requirements", ["crop_id"], unique=False)
    op.create_index(op.f("ix_farm_water_requirements_stage_id"), "farm_water_requirements", ["stage_id"], unique=False)
    op.create_index(op.f("ix_farm_water_requirements_status"), "farm_water_requirements", ["status"], unique=False)

    op.create_table(
        "water_assessment_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("estimated_requirement_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("rainfall_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("deficit_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("surplus_mm", sa.Numeric(8, 2), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.ForeignKeyConstraint(["stage_id"], ["crop_stages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_water_assessment_history_id"), "water_assessment_history", ["id"], unique=False)
    op.create_index(op.f("ix_water_assessment_history_farm_id"), "water_assessment_history", ["farm_id"], unique=False)
    op.create_index(op.f("ix_water_assessment_history_crop_id"), "water_assessment_history", ["crop_id"], unique=False)
    op.create_index(op.f("ix_water_assessment_history_stage_id"), "water_assessment_history", ["stage_id"], unique=False)
    op.create_index(op.f("ix_water_assessment_history_status"), "water_assessment_history", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_water_assessment_history_status"), table_name="water_assessment_history")
    op.drop_index(op.f("ix_water_assessment_history_stage_id"), table_name="water_assessment_history")
    op.drop_index(op.f("ix_water_assessment_history_crop_id"), table_name="water_assessment_history")
    op.drop_index(op.f("ix_water_assessment_history_farm_id"), table_name="water_assessment_history")
    op.drop_index(op.f("ix_water_assessment_history_id"), table_name="water_assessment_history")
    op.drop_table("water_assessment_history")

    op.drop_index(op.f("ix_farm_water_requirements_status"), table_name="farm_water_requirements")
    op.drop_index(op.f("ix_farm_water_requirements_stage_id"), table_name="farm_water_requirements")
    op.drop_index(op.f("ix_farm_water_requirements_crop_id"), table_name="farm_water_requirements")
    op.drop_index(op.f("ix_farm_water_requirements_farm_id"), table_name="farm_water_requirements")
    op.drop_index(op.f("ix_farm_water_requirements_id"), table_name="farm_water_requirements")
    op.drop_table("farm_water_requirements")

    op.drop_index(op.f("ix_crop_water_profiles_stage_id"), table_name="crop_water_profiles")
    op.drop_index(op.f("ix_crop_water_profiles_crop_id"), table_name="crop_water_profiles")
    op.drop_index(op.f("ix_crop_water_profiles_id"), table_name="crop_water_profiles")
    op.drop_table("crop_water_profiles")
