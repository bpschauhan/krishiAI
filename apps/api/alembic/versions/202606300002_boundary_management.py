"""add boundary lifecycle audit fields

Revision ID: 202606300002
Revises: 202606300001
Create Date: 2026-06-30 22:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606300002"
down_revision: str | None = "202606300001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "farm_boundaries",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "plot_boundaries",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "geo_regions",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("geo_regions", "updated_at")
    op.drop_column("plot_boundaries", "updated_at")
    op.drop_column("farm_boundaries", "updated_at")
