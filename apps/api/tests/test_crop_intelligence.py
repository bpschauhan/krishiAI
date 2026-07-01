import json
from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.crop_intelligence import get_crop_intelligence_service
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.crop_intelligence import CropSeason, CropSuitabilityAssessment, CropSuitabilityProfile
from app.models.disease import Crop
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.geospatial import FarmBoundary
from app.models.language import Language
from app.models.location import District
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.services.crop_intelligence import (
    CropIntelligenceService,
    CropSuitabilityEngine,
    SeasonResolver,
    SuitabilityWeather,
)
from app.services.crop_intelligence_seed import seed_crop_intelligence_catalog
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


class FixedKharifResolver(SeasonResolver):
    def resolve(self, on_date: date | None = None):
        return "Kharif"


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
        seed_disease_catalog(session)
        seed_crop_intelligence_catalog(session)
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
                    temperature_c=Decimal("31.00"),
                    humidity_percent=Decimal("70.00"),
                    rainfall_mm=Decimal("6.00"),
                    wind_speed_kmh=Decimal("8.00"),
                    pressure_hpa=Decimal("1005.00"),
                    cloud_cover_percent=Decimal("65.00"),
                ),
                DailyForecast(
                    location_id=location.id,
                    provider="test",
                    forecast_date=date(2026, 7, 1),
                    temperature_min_c=Decimal("24.00"),
                    temperature_max_c=Decimal("32.00"),
                    humidity_percent=Decimal("72.00"),
                    rainfall_mm=Decimal("7.50"),
                    wind_speed_kmh=Decimal("10.00"),
                    pressure_hpa=Decimal("1004.00"),
                    cloud_cover_percent=Decimal("70.00"),
                ),
            ]
        )
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_crop_intelligence_service] = lambda: CropIntelligenceService(resolver=FixedKharifResolver())
    return TestClient(app)


def test_season_resolution() -> None:
    resolver = SeasonResolver()

    assert resolver.resolve(date(2026, 7, 1)) == "Kharif"
    assert resolver.resolve(date(2026, 12, 1)) == "Rabi"
    assert resolver.resolve(date(2026, 4, 15)) == "Zaid"


def test_suitability_scoring_and_matching() -> None:
    profile = CropSuitabilityProfile(
        crop_id=1,
        min_temperature=Decimal("20.00"),
        max_temperature=Decimal("38.00"),
        min_rainfall=Decimal("4.00"),
        max_rainfall=Decimal("12.00"),
        preferred_soil_type="Clay loam",
    )
    seasons = [CropSeason(crop_id=1, season_name="Rice Kharif", season_type="Kharif")]

    result = CropSuitabilityEngine().calculate(
        profile,
        SuitabilityWeather(temperature_c=Decimal("31.00"), rainfall_mm=Decimal("7.50")),
        "Kharif",
        seasons,
    )

    assert result.suitability_score == 100
    assert result.weather_match is True
    assert result.rainfall_match is True
    assert result.temperature_match is True


def test_suitability_scoring_penalizes_weather_mismatch() -> None:
    profile = CropSuitabilityProfile(
        crop_id=1,
        min_temperature=Decimal("20.00"),
        max_temperature=Decimal("38.00"),
        min_rainfall=Decimal("4.00"),
        max_rainfall=Decimal("12.00"),
        preferred_soil_type="Clay loam",
    )
    seasons = [CropSeason(crop_id=1, season_name="Rice Kharif", season_type="Kharif")]

    result = CropSuitabilityEngine().calculate(
        profile,
        SuitabilityWeather(temperature_c=Decimal("42.00"), rainfall_mm=Decimal("1.00")),
        "Rabi",
        seasons,
    )

    assert result.suitability_score < 100
    assert result.weather_match is False
    assert result.rainfall_match is False
    assert result.temperature_match is False


def test_crop_intelligence_apis_return_catalog_and_assessment() -> None:
    client = build_client()
    with TestingSessionLocal() as session:
        rice = session.scalar(select(Crop).where(Crop.name == "Rice"))
        assert rice is not None

    seasons = client.get("/api/v1/crop-seasons")
    calendar = client.get("/api/v1/crop-calendar?district_id=1")
    suitability = client.get(f"/api/v1/crop-suitability?farm_id=1&crop_id={rice.id}")

    assert seasons.status_code == 200
    assert {"Rice", "Wheat", "Potato", "Sugarcane", "Maize", "Mustard"}.issubset(
        {item["crop_name"] for item in seasons.json()}
    )
    assert calendar.status_code == 200
    assert any(item["crop_name"] == "Rice" for item in calendar.json())
    assert suitability.status_code == 200
    payload = suitability.json()
    assert payload["crop_name"] == "Rice"
    assert payload["district_name"] == "Lucknow"
    assert payload["season"] == "Kharif"
    assert payload["suitability_score"] == 100
    assert payload["weather_match"] is True
    assert payload["rainfall_match"] is True
    assert payload["temperature_match"] is True

    with TestingSessionLocal() as session:
        history = session.scalars(select(CropSuitabilityAssessment)).all()
        assert len(history) == 1
        assert history[0].suitability_score == 100
        assert history[0].season == "Kharif"


def test_crop_calendar_validates_district() -> None:
    client = build_client()

    response = client.get("/api/v1/crop-calendar?district_id=999")

    assert response.status_code == 404
    assert "District not found" in response.text


def _farm_boundary(farm_id: int) -> FarmBoundary:
    area = calculate_polygon_area(FARM_POLYGON["coordinates"])
    return FarmBoundary(
        farm_id=farm_id,
        geometry=json.dumps(FARM_POLYGON, separators=(",", ":")),
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
