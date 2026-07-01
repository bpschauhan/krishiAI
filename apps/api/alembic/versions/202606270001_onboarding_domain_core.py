"""create onboarding domain core tables

Revision ID: 202606270001
Revises: 202606260001
Create Date: 2026-06-27 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606270001"
down_revision: str | None = "202606260001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_languages_id"), "languages", ["id"], unique=False)
    op.create_index(op.f("ix_languages_code"), "languages", ["code"], unique=True)
    op.create_unique_constraint(op.f("uq_languages_name"), "languages", ["name"])

    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "state", name="uq_district_name_state"),
    )
    op.create_index(op.f("ix_districts_id"), "districts", ["id"], unique=False)
    op.create_index(op.f("ix_districts_name"), "districts", ["name"], unique=False)

    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone_number", sa.String(length=16), nullable=False),
        sa.Column("village", sa.String(length=160), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("language_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["language_id"], ["languages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farmers_id"), "farmers", ["id"], unique=False)
    op.create_index(op.f("ix_farmers_phone_number"), "farmers", ["phone_number"], unique=True)

    op.create_table(
        "farms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("village", sa.String(length=160), nullable=False),
        sa.Column("total_acreage", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farms_id"), "farms", ["id"], unique=False)
    op.create_index(op.f("ix_farms_farmer_id"), "farms", ["farmer_id"], unique=False)

    op.create_table(
        "plots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("acreage", sa.Numeric(10, 2), nullable=False),
        sa.Column("current_crop", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plots_id"), "plots", ["id"], unique=False)
    op.create_index(op.f("ix_plots_farm_id"), "plots", ["farm_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plots_farm_id"), table_name="plots")
    op.drop_index(op.f("ix_plots_id"), table_name="plots")
    op.drop_table("plots")

    op.drop_index(op.f("ix_farms_farmer_id"), table_name="farms")
    op.drop_index(op.f("ix_farms_id"), table_name="farms")
    op.drop_table("farms")

    op.drop_index(op.f("ix_farmers_phone_number"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_id"), table_name="farmers")
    op.drop_table("farmers")

    op.drop_index(op.f("ix_districts_name"), table_name="districts")
    op.drop_index(op.f("ix_districts_id"), table_name="districts")
    op.drop_table("districts")

    op.drop_constraint(op.f("uq_languages_name"), "languages", type_="unique")
    op.drop_index(op.f("ix_languages_code"), table_name="languages")
    op.drop_index(op.f("ix_languages_id"), table_name="languages")
    op.drop_table("languages")
