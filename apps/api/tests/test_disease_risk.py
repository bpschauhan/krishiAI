import json
from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.disease import Crop, CropDisease, CropStage, DiseaseRiskAssessment
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.geospatial import FarmBoundary
from app.models.language import Language
from app.models.location import District
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.services.disease_risk import DiseaseRuleEngine, WeatherRiskInput, risk_level_for_score
from app.services.disease_seed import seed_disease_catalog
from app.utils.geo import calculate_polygon_area

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FARM_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.92, 26.95],
            [80.96, 26.95],
            [80.96, 26.99],
            [80.92, 26.99],
            [80.92, 26.95],
        ]
    ],
}


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
        seed_disease_catalog(session)
        language = Language(id=1, code="hi", name="Hindi", is_active=True)
        district = District(id=1, name="Lucknow", state="Uttar Pradesh", is_active=True)
        farmer = Farmer(
            id=1,
            full_name="Ramesh Kumar",
            phone_number="9876543210",
            village="Semra",
            district_id=1,
            language_id=1,
        )
        farm = Farm(
            id=1,
            farmer_id=1,
            district_id=1,
            name="North Field",
            village="Semra",
            total_acreage=Decimal("2.50"),
        )
        session.add_all([language, district, farmer, farm, _farm_boundary(1)])
        session.flush()
        location = WeatherLocation(
            farm_id=1,
            name="North Field",
            latitude=Decimal("26.970000"),
            longitude=Decimal("80.940000"),
            source="farm_boundary",
        )
        session.add(location)
        session.flush()
        session.add_all(
            [
                CurrentWeather(
                    location_id=location.id,
                    provider="test",
                    observed_at=datetime(2026, 7, 1, 6, tzinfo=timezone.utc),
                    temperature_c=Decimal("27.00"),
                    humidity_percent=Decimal("88.00"),
                    rainfall_mm=Decimal("2.50"),
                    wind_speed_kmh=Decimal("8.00"),
                    pressure_hpa=Decimal("1005.00"),
                    cloud_cover_percent=Decimal("75.00"),
                ),
                DailyForecast(
                    location_id=location.id,
                    provider="test",
                    forecast_date=date(2026, 7, 1),
                    temperature_min_c=Decimal("24.00"),
                    temperature_max_c=Decimal("31.00"),
                    humidity_percent=Decimal("86.00"),
                    rainfall_mm=Decimal("4.00"),
                    wind_speed_kmh=Decimal("10.00"),
                    pressure_hpa=Decimal("1004.00"),
                    cloud_cover_percent=Decimal("82.00"),
                ),
            ]
        )
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_risk_level_mapping() -> None:
    assert risk_level_for_score(0) == "Low"
    assert risk_level_for_score(30) == "Low"
    assert risk_level_for_score(31) == "Medium"
    assert risk_level_for_score(70) == "Medium"
    assert risk_level_for_score(71) == "High"
    assert risk_level_for_score(100) == "High"


def test_rule_engine_scores_weather_and_stage_factors() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        seed_disease_catalog(session)
        crop = session.scalar(select(Crop).where(Crop.name == "Rice"))
        disease = session.scalar(select(CropDisease).where(CropDisease.name == "Blast"))
        stage = session.scalar(select(CropStage).where(CropStage.name == "Tillering"))

        assert crop is not None
        assert disease is not None
        assert stage is not None

        score = DiseaseRuleEngine().calculate_risk(
            crop,
            disease,
            stage,
            WeatherRiskInput(temperature_c=27, humidity_percent=88, rainfall_mm=3),
        )

    assert score.score == 100
    assert score.level == "High"
    assert "high humidity" in score.contributing_factors
    assert "recent or forecast rainfall" in score.contributing_factors


def test_disease_risk_api_returns_scores_and_persists_history() -> None:
    client = build_client()
    with TestingSessionLocal() as session:
        crop = session.scalar(select(Crop).where(Crop.name == "Rice"))
        stage = session.scalar(select(CropStage).where(CropStage.crop_id == crop.id, CropStage.name == "Tillering"))
        assert crop is not None
        assert stage is not None
        crop_id = crop.id
        stage_id = stage.id

    response = client.get(f"/api/v1/disease-risk?farm_id=1&crop_id={crop_id}&crop_stage_id={stage_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "High"
    assert payload["risk_score"] >= 71
    assert {result["disease_name"] for result in payload["disease_results"]} == {"Blast", "Brown Spot"}
    assert all(result["contributing_factors"] for result in payload["disease_results"])

    with TestingSessionLocal() as session:
        history = session.scalars(select(DiseaseRiskAssessment)).all()
        assert len(history) == 2
        assert {record.level for record in history} == {"High"}


def test_disease_risk_api_validates_crop_stage_relationship() -> None:
    client = build_client()
    with TestingSessionLocal() as session:
        rice = session.scalar(select(Crop).where(Crop.name == "Rice"))
        wheat_stage = session.scalar(select(CropStage).join(Crop).where(Crop.name == "Wheat"))
        assert rice is not None
        assert wheat_stage is not None

    response = client.get(f"/api/v1/disease-risk?farm_id=1&crop_id={rice.id}&crop_stage_id={wheat_stage.id}")

    assert response.status_code == 404
    assert "Crop stage not found" in response.text


def _farm_boundary(farm_id: int) -> FarmBoundary:
    area = calculate_polygon_area(FARM_POLYGON["coordinates"])
    return FarmBoundary(
        farm_id=farm_id,
        geometry=json.dumps(FARM_POLYGON, separators=(",", ":")),
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
