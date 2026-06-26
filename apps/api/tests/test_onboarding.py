from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.language import Language
from app.models.location import District


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


def build_client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        session.add_all(
            [
                Language(id=1, code="hi", name="Hindi", is_active=True),
                Language(id=2, code="en", name="English", is_active=True),
                District(id=1, name="Lucknow", state="Uttar Pradesh", is_active=True),
                District(id=2, name="Inactive", state="Uttar Pradesh", is_active=False),
            ]
        )
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_onboarding_routes_create_and_read_profile() -> None:
    client = build_client()

    districts_response = client.get("/api/v1/districts")
    assert districts_response.status_code == 200
    assert districts_response.json() == [{"id": 1, "name": "Lucknow", "state": "Uttar Pradesh"}]

    languages_response = client.get("/api/v1/languages")
    assert languages_response.status_code == 200
    assert languages_response.json() == [
        {"id": 2, "code": "en", "name": "English"},
        {"id": 1, "code": "hi", "name": "Hindi"},
    ]

    farmer_response = client.post(
        "/api/v1/farmers",
        json={
            "full_name": "Ramesh Kumar",
            "phone_number": "+919876543210",
            "village": "Semra",
            "district_id": 1,
            "language_id": 1,
        },
    )
    assert farmer_response.status_code == 201
    farmer = farmer_response.json()
    assert farmer["phone_number"] == "9876543210"

    farm_response = client.post(
        "/api/v1/farms",
        json={
            "farmer_id": farmer["id"],
            "district_id": 1,
            "name": "North Field",
            "village": "Semra",
            "total_acreage": "2.50",
        },
    )
    assert farm_response.status_code == 201
    farm = farm_response.json()

    plot_response = client.post(
        "/api/v1/plots",
        json={
            "farm_id": farm["id"],
            "name": "Plot A",
            "acreage": "1.25",
            "current_crop": "Wheat",
        },
    )
    assert plot_response.status_code == 201

    detail_response = client.get(f"/api/v1/farmers/{farmer['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["full_name"] == "Ramesh Kumar"
    assert detail["district"]["name"] == "Lucknow"
    assert detail["language"]["code"] == "hi"
    assert detail["farm_count"] == 1
    assert detail["plot_count"] == 1


def test_onboarding_validation_errors_are_returned() -> None:
    client = build_client()

    farmer_response = client.post(
        "/api/v1/farmers",
        json={
            "full_name": "Ramesh Kumar",
            "phone_number": "12345",
            "village": "Semra",
            "district_id": 1,
            "language_id": 1,
        },
    )
    assert farmer_response.status_code == 422

    farm_response = client.post(
        "/api/v1/farms",
        json={
            "farmer_id": 1,
            "district_id": 1,
            "name": "North Field",
            "village": "Semra",
            "total_acreage": "0",
        },
    )
    assert farm_response.status_code == 422
