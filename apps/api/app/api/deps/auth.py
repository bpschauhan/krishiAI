from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import ClerkClaims, verify_clerk_jwt
from app.db.session import get_db
from app.models.auth import Permission, Role, User
from app.schemas.auth import PermissionRead, RoleRead, UserRead

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_claims(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ClerkClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cached_claims = getattr(request.state, "auth_claims", None)
    if isinstance(cached_claims, ClerkClaims):
        return cached_claims

    return verify_clerk_jwt(credentials.credentials)


def _user_query(clerk_user_id: str):
    return (
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.roles).selectinload(Role.permissions),
        )
        .where(User.clerk_user_id == clerk_user_id)
    )


def get_current_user(
    claims: ClerkClaims = Depends(get_auth_claims),
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(_user_query(claims.subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user is not synchronized",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def list_user_permissions(user: User) -> list[Permission]:
    permissions_by_slug: dict[str, Permission] = {}
    for role in user.roles:
        if not role.is_active:
            continue
        for permission in role.permissions:
            if permission.is_active:
                permissions_by_slug[permission.slug] = permission
    return sorted(permissions_by_slug.values(), key=lambda permission: permission.slug)


def user_has_permission(user: User, permission_slug: str) -> bool:
    return any(permission.slug == permission_slug for permission in list_user_permissions(user))


def require_permission(permission_slug: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_has_permission(current_user, permission_slug):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def ensure_owner_or_permission(user: User, owner_user_id: int, permission_slug: str) -> None:
    if user.id == owner_user_id:
        return
    if user_has_permission(user, permission_slug):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource ownership required")


def serialize_user(user: User) -> UserRead:
    permissions = list_user_permissions(user)
    return UserRead(
        id=user.id,
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        profile=user.profile,
        roles=[RoleRead.model_validate(role) for role in sorted(user.roles, key=lambda role: role.slug)],
        permissions=[PermissionRead.model_validate(permission) for permission in permissions],
    )
