"""create disease risk engine tables

Revision ID: 202607010002
Revises: 202607010001
Create Date: 2026-07-01 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607010002"
down_revision: str | None = "202607010001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("scientific_name", sa.String(length=180), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_crops_name"),
    )
    op.create_index(op.f("ix_crops_id"), "crops", ["id"], unique=False)
    op.create_index(op.f("ix_crops_name"), "crops", ["name"], unique=False)

    op.create_table(
        "crop_diseases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("severity_scale", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "name", name="uq_crop_diseases_crop_id_name"),
    )
    op.create_index(op.f("ix_crop_diseases_id"), "crop_diseases", ["id"], unique=False)
    op.create_index(op.f("ix_crop_diseases_crop_id"), "crop_diseases", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_diseases_name"), "crop_diseases", ["name"], unique=False)

    op.create_table(
        "crop_stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crop_id", "name", name="uq_crop_stages_crop_id_name"),
    )
    op.create_index(op.f("ix_crop_stages_id"), "crop_stages", ["id"], unique=False)
    op.create_index(op.f("ix_crop_stages_crop_id"), "crop_stages", ["crop_id"], unique=False)
    op.create_index(op.f("ix_crop_stages_name"), "crop_stages", ["name"], unique=False)

    op.create_table(
        "disease_risk_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("crop_id", sa.Integer(), nullable=False),
        sa.Column("crop_stage_id", sa.Integer(), nullable=False),
        sa.Column("disease_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("level", sa.String(length=24), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"]),
        sa.ForeignKeyConstraint(["crop_stage_id"], ["crop_stages.id"]),
        sa.ForeignKeyConstraint(["disease_id"], ["crop_diseases.id"]),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_disease_risk_assessments_id"), "disease_risk_assessments", ["id"], unique=False)
    op.create_index(op.f("ix_disease_risk_assessments_farm_id"), "disease_risk_assessments", ["farm_id"], unique=False)
    op.create_index(op.f("ix_disease_risk_assessments_crop_id"), "disease_risk_assessments", ["crop_id"], unique=False)
    op.create_index(op.f("ix_disease_risk_assessments_crop_stage_id"), "disease_risk_assessments", ["crop_stage_id"], unique=False)
    op.create_index(op.f("ix_disease_risk_assessments_disease_id"), "disease_risk_assessments", ["disease_id"], unique=False)
    op.create_index(op.f("ix_disease_risk_assessments_level"), "disease_risk_assessments", ["level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_disease_risk_assessments_level"), table_name="disease_risk_assessments")
    op.drop_index(op.f("ix_disease_risk_assessments_disease_id"), table_name="disease_risk_assessments")
    op.drop_index(op.f("ix_disease_risk_assessments_crop_stage_id"), table_name="disease_risk_assessments")
    op.drop_index(op.f("ix_disease_risk_assessments_crop_id"), table_name="disease_risk_assessments")
    op.drop_index(op.f("ix_disease_risk_assessments_farm_id"), table_name="disease_risk_assessments")
    op.drop_index(op.f("ix_disease_risk_assessments_id"), table_name="disease_risk_assessments")
    op.drop_table("disease_risk_assessments")

    op.drop_index(op.f("ix_crop_stages_name"), table_name="crop_stages")
    op.drop_index(op.f("ix_crop_stages_crop_id"), table_name="crop_stages")
    op.drop_index(op.f("ix_crop_stages_id"), table_name="crop_stages")
    op.drop_table("crop_stages")

    op.drop_index(op.f("ix_crop_diseases_name"), table_name="crop_diseases")
    op.drop_index(op.f("ix_crop_diseases_crop_id"), table_name="crop_diseases")
    op.drop_index(op.f("ix_crop_diseases_id"), table_name="crop_diseases")
    op.drop_table("crop_diseases")

    op.drop_index(op.f("ix_crops_name"), table_name="crops")
    op.drop_index(op.f("ix_crops_id"), table_name="crops")
    op.drop_table("crops")
