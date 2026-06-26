from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps.auth import (
    get_auth_claims,
    get_current_user,
    require_permission,
    serialize_user,
)
from app.core.config import settings
from app.core.security import ClerkClaims
from app.db.session import get_db
from app.models.auth import Permission, Role, User, UserProfile, UserRole
from app.schemas.auth import (
    AuthSyncRequest,
    PermissionRead,
    RoleRead,
    UserProfileUpdate,
    UserRead,
)

router = APIRouter()


@router.post("/auth/sync", response_model=UserRead)
def sync_authenticated_user(
    payload: AuthSyncRequest,
    claims: ClerkClaims = Depends(get_auth_claims),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.scalar(
        select(User)
        .options(selectinload(User.profile), selectinload(User.roles).selectinload(Role.permissions))
        .where(User.clerk_user_id == claims.subject)
    )

    if payload.email:
        existing_email_user = db.scalar(
            select(User).where(User.email == str(payload.email), User.clerk_user_id != claims.subject)
        )
        if existing_email_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already linked to another user",
            )

    if user is None:
        user = User(
            clerk_user_id=claims.subject,
            email=str(payload.email) if payload.email else _claim_string(claims, "email"),
            first_name=payload.first_name or _claim_string(claims, "first_name"),
            last_name=payload.last_name or _claim_string(claims, "last_name"),
            is_active=True,
            last_synced_at=datetime.now(UTC),
        )
        db.add(user)
        db.flush()
    else:
        user.email = str(payload.email) if payload.email else user.email or _claim_string(claims, "email")
        user.first_name = payload.first_name if payload.first_name is not None else user.first_name
        user.last_name = payload.last_name if payload.last_name is not None else user.last_name
        user.last_synced_at = datetime.now(UTC)

    if user.profile is None:
        user.profile = UserProfile(
            display_name=payload.display_name,
            phone_number=payload.phone_number,
        )
    else:
        user.profile.display_name = payload.display_name if payload.display_name is not None else user.profile.display_name
        user.profile.phone_number = payload.phone_number if payload.phone_number is not None else user.profile.phone_number

    if not user.roles:
        default_role = db.scalar(
            select(Role).where(Role.slug == settings.CLERK_DEFAULT_ROLE_SLUG, Role.is_active.is_(True))
        )
        if default_role is not None:
            db.add(UserRole(user_id=user.id, role_id=default_role.id))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User synchronization conflict") from exc

    db.refresh(user)
    user = db.scalar(
        select(User)
        .options(selectinload(User.profile), selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user.id)
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after sync")
    return serialize_user(user)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return serialize_user(current_user)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(require_permission("profile:update")),
    db: Session = Depends(get_db),
) -> UserRead:
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name

    if current_user.profile is None:
        current_user.profile = UserProfile()

    profile = current_user.profile
    for field_name in ("display_name", "phone_number", "preferred_language", "district", "village"):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(profile, field_name, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    current_user = db.scalar(
        select(User)
        .options(selectinload(User.profile), selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == current_user.id)
    )
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return serialize_user(current_user)


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    _: User = Depends(require_permission("roles:read")),
    db: Session = Depends(get_db),
) -> list[Role]:
    return list(db.scalars(select(Role).where(Role.is_active.is_(True)).order_by(Role.name)))


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(
    _: User = Depends(require_permission("permissions:read")),
    db: Session = Depends(get_db),
) -> list[Permission]:
    return list(db.scalars(select(Permission).where(Permission.is_active.is_(True)).order_by(Permission.slug)))


def _claim_string(claims: ClerkClaims, key: str) -> str | None:
    value = claims.payload.get(key)
    return value if isinstance(value, str) and value else None
