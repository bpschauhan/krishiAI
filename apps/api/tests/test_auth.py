from collections.abc import Generator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import auth as auth_deps
from app.core import security
from app.core.security import ClerkClaims, verify_clerk_jwt
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.auth import Role, User, UserRole
from app.services.auth_seed import seed_auth_catalog


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_claims() -> ClerkClaims:
    return ClerkClaims(
        subject="user_test123",
        payload={
            "sub": "user_test123",
            "email": "farmer@example.com",
            "first_name": "Ramesh",
            "last_name": "Kumar",
        },
    )


def build_client(authenticated: bool = True) -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        seed_auth_catalog(session)
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    if authenticated:
        app.dependency_overrides[auth_deps.get_auth_claims] = override_claims
    return TestClient(app)


def test_auth_sync_creates_user_profile_and_default_farmer_role() -> None:
    client = build_client()

    response = client.post(
        "/api/v1/auth/sync",
        json={
            "email": "farmer@example.com",
            "first_name": "Ramesh",
            "last_name": "Kumar",
            "display_name": "Ramesh Kumar",
            "phone_number": "+919876543210",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["clerk_user_id"] == "user_test123"
    assert payload["profile"]["phone_number"] == "9876543210"
    assert [role["slug"] for role in payload["roles"]] == ["farmer"]
    assert "dashboard:read" in {permission["slug"] for permission in payload["permissions"]}


def test_me_and_profile_update_require_authenticated_synced_user() -> None:
    client = build_client()
    client.post("/api/v1/auth/sync", json={"email": "farmer@example.com"})

    me_response = client.get("/api/v1/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "farmer@example.com"

    update_response = client.patch(
        "/api/v1/me",
        json={
            "display_name": "Updated Farmer",
            "phone_number": "9876543210",
            "preferred_language": "Hindi",
            "district": "Lucknow",
            "village": "Semra",
        },
    )
    assert update_response.status_code == 200
    profile = update_response.json()["profile"]
    assert profile["display_name"] == "Updated Farmer"
    assert profile["district"] == "Lucknow"


def test_roles_and_permissions_are_database_permission_protected() -> None:
    client = build_client()
    client.post("/api/v1/auth/sync", json={"email": "farmer@example.com"})

    farmer_roles_response = client.get("/api/v1/roles")
    assert farmer_roles_response.status_code == 403

    with TestingSessionLocal() as session:
        user = session.scalar(select(User).where(User.clerk_user_id == "user_test123"))
        role = session.scalar(select(Role).where(Role.slug == "super_admin"))
        assert user is not None
        assert role is not None
        session.add(UserRole(user_id=user.id, role_id=role.id))
        session.commit()

    roles_response = client.get("/api/v1/roles")
    permissions_response = client.get("/api/v1/permissions")

    assert roles_response.status_code == 200
    assert "super_admin" in {role["slug"] for role in roles_response.json()}
    assert permissions_response.status_code == 200
    assert "admin:access" in {permission["slug"] for permission in permissions_response.json()}


def test_protected_endpoint_rejects_missing_bearer_token() -> None:
    client = build_client(authenticated=False)

    response = client.get("/api/v1/me")

    assert response.status_code == 401


def test_malformed_clerk_jwt_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    security._get_jwks_client.cache_clear()
    monkeypatch.setattr(security.settings, "CLERK_ISSUER_URL", "https://example.clerk.accounts.dev")
    monkeypatch.setattr(security.settings, "CLERK_JWKS_URL", "https://example.clerk.accounts.dev/.well-known/jwks.json")

    with pytest.raises(HTTPException) as exc:
        verify_clerk_jwt("not-a-jwt")

    assert exc.value.status_code == 401
