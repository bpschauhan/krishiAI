from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import Permission, PermissionRole, Role

SYSTEM_PERMISSIONS: tuple[dict[str, str], ...] = (
    {"slug": "profile:read", "name": "Read profile", "description": "View own identity profile"},
    {"slug": "profile:update", "name": "Update profile", "description": "Update own identity profile"},
    {"slug": "roles:read", "name": "Read roles", "description": "View configured roles"},
    {"slug": "permissions:read", "name": "Read permissions", "description": "View configured permissions"},
    {"slug": "farmers:read", "name": "Read farmers", "description": "View farmer records"},
    {"slug": "farmers:write", "name": "Write farmers", "description": "Create and update farmer records"},
    {"slug": "farms:read", "name": "Read farms", "description": "View farm records"},
    {"slug": "farms:write", "name": "Write farms", "description": "Create and update farm records"},
    {"slug": "plots:read", "name": "Read plots", "description": "View plot records"},
    {"slug": "plots:write", "name": "Write plots", "description": "Create and update plot records"},
    {"slug": "dashboard:read", "name": "Read dashboard", "description": "View dashboard data"},
    {"slug": "admin:access", "name": "Admin access", "description": "Access administrative controls"},
)

SYSTEM_ROLES: tuple[dict[str, str], ...] = (
    {"slug": "farmer", "name": "Farmer", "description": "Farmer account owner"},
    {"slug": "agronomist", "name": "Agronomist", "description": "Agronomy advisor"},
    {"slug": "fpo_admin", "name": "FPO Admin", "description": "Farmer producer organization administrator"},
    {"slug": "government_officer", "name": "Government Officer", "description": "Government oversight user"},
    {"slug": "super_admin", "name": "Super Admin", "description": "Platform administrator"},
)

ROLE_PERMISSION_SLUGS: dict[str, tuple[str, ...]] = {
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
    "super_admin": tuple(permission["slug"] for permission in SYSTEM_PERMISSIONS),
}


def seed_auth_catalog(session: Session) -> None:
    existing_permissions = {
        permission.slug: permission for permission in session.scalars(select(Permission)).all()
    }
    for permission_data in SYSTEM_PERMISSIONS:
        permission = existing_permissions.get(permission_data["slug"])
        if permission is None:
            permission = Permission(**permission_data, is_active=True)
            session.add(permission)
            existing_permissions[permission.slug] = permission
        else:
            permission.name = permission_data["name"]
            permission.description = permission_data["description"]
            permission.is_active = True

    existing_roles = {role.slug: role for role in session.scalars(select(Role)).all()}
    for role_data in SYSTEM_ROLES:
        role = existing_roles.get(role_data["slug"])
        if role is None:
            role = Role(**role_data, is_system=True, is_active=True)
            session.add(role)
            existing_roles[role.slug] = role
        else:
            role.name = role_data["name"]
            role.description = role_data["description"]
            role.is_system = True
            role.is_active = True

    session.flush()

    existing_links = {
        (link.role_id, link.permission_id)
        for link in session.scalars(select(PermissionRole)).all()
    }
    for role_slug, permission_slugs in ROLE_PERMISSION_SLUGS.items():
        role = existing_roles[role_slug]
        for permission_slug in permission_slugs:
            permission = existing_permissions[permission_slug]
            link_key = (role.id, permission.id)
            if link_key not in existing_links:
                session.add(PermissionRole(role_id=role.id, permission_id=permission.id))
                existing_links.add(link_key)
