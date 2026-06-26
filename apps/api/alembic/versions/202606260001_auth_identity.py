"""create auth identity and rbac tables

Revision ID: 202606260001
Revises:
Create Date: 2026-06-26 20:02:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606260001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = (
    ("profile:read", "Read profile", "View own identity profile"),
    ("profile:update", "Update profile", "Update own identity profile"),
    ("roles:read", "Read roles", "View configured roles"),
    ("permissions:read", "Read permissions", "View configured permissions"),
    ("farmers:read", "Read farmers", "View farmer records"),
    ("farmers:write", "Write farmers", "Create and update farmer records"),
    ("farms:read", "Read farms", "View farm records"),
    ("farms:write", "Write farms", "Create and update farm records"),
    ("plots:read", "Read plots", "View plot records"),
    ("plots:write", "Write plots", "Create and update plot records"),
    ("dashboard:read", "Read dashboard", "View dashboard data"),
    ("admin:access", "Admin access", "Access administrative controls"),
)

ROLES = (
    ("farmer", "Farmer", "Farmer account owner"),
    ("agronomist", "Agronomist", "Agronomy advisor"),
    ("fpo_admin", "FPO Admin", "Farmer producer organization administrator"),
    ("government_officer", "Government Officer", "Government oversight user"),
    ("super_admin", "Super Admin", "Platform administrator"),
)

ROLE_PERMISSIONS = {
    "farmer": (
        "profile:read",
        "profile:update",
        "farmers:read",
        "farmers:write",
        "farms:read",
        "farms:write",
        "plots:read",
        "plots:write",
        "dashboard:read",
    ),
    "agronomist": (
        "profile:read",
        "profile:update",
        "farmers:read",
        "farms:read",
        "plots:read",
        "dashboard:read",
    ),
    "fpo_admin": (
        "profile:read",
        "profile:update",
        "roles:read",
        "permissions:read",
        "farmers:read",
        "farmers:write",
        "farms:read",
        "farms:write",
        "plots:read",
        "plots:write",
        "dashboard:read",
    ),
    "government_officer": (
        "profile:read",
        "profile:update",
        "roles:read",
        "permissions:read",
        "farmers:read",
        "farms:read",
        "plots:read",
        "dashboard:read",
    ),
    "super_admin": tuple(permission[0] for permission in PERMISSIONS),
}


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clerk_user_id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_clerk_user_id"), "users", ["clerk_user_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_slug"), "roles", ["slug"], unique=True)
    op.create_unique_constraint(op.f("uq_roles_name"), "roles", ["name"])

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
    op.create_index(op.f("ix_permissions_slug"), "permissions", ["slug"], unique=True)
    op.create_unique_constraint(op.f("uq_permissions_name"), "permissions", ["name"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("phone_number", sa.String(length=16), nullable=True),
        sa.Column("preferred_language", sa.String(length=32), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("village", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_profiles_id"), "user_profiles", ["id"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index(op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False)
    op.create_index(op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False)

    op.create_table(
        "permission_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("permission_id", "role_id", name="uq_permission_role"),
    )
    op.create_index(op.f("ix_permission_roles_permission_id"), "permission_roles", ["permission_id"], unique=False)
    op.create_index(op.f("ix_permission_roles_role_id"), "permission_roles", ["role_id"], unique=False)

    _insert_rbac_catalog()


def downgrade() -> None:
    op.drop_index(op.f("ix_permission_roles_role_id"), table_name="permission_roles")
    op.drop_index(op.f("ix_permission_roles_permission_id"), table_name="permission_roles")
    op.drop_table("permission_roles")
    op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_role_id"), table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index(op.f("ix_user_profiles_id"), table_name="user_profiles")
    op.drop_table("user_profiles")
    op.drop_constraint(op.f("uq_permissions_name"), "permissions", type_="unique")
    op.drop_index(op.f("ix_permissions_slug"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_id"), table_name="permissions")
    op.drop_table("permissions")
    op.drop_constraint(op.f("uq_roles_name"), "roles", type_="unique")
    op.drop_index(op.f("ix_roles_slug"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_clerk_user_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")


def _insert_rbac_catalog() -> None:
    role_table = sa.table(
        "roles",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_system", sa.Boolean),
        sa.column("is_active", sa.Boolean),
    )
    permission_table = sa.table(
        "permissions",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        role_table,
        [
            {"slug": slug, "name": name, "description": description, "is_system": True, "is_active": True}
            for slug, name, description in ROLES
        ],
    )
    op.bulk_insert(
        permission_table,
        [
            {"slug": slug, "name": name, "description": description, "is_active": True}
            for slug, name, description in PERMISSIONS
        ],
    )

    bind = op.get_bind()
    role_ids = dict(bind.execute(sa.text("select slug, id from roles")).all())
    permission_ids = dict(bind.execute(sa.text("select slug, id from permissions")).all())
    permission_role_table = sa.table(
        "permission_roles",
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )
    op.bulk_insert(
        permission_role_table,
        [
            {"role_id": role_ids[role_slug], "permission_id": permission_ids[permission_slug]}
            for role_slug, permission_slugs in ROLE_PERMISSIONS.items()
            for permission_slug in permission_slugs
        ],
    )
