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
from app.models.disease import Crop, CropStage
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.geospatial import FarmBoundary
from app.models.language import Language
from app.models.location import District
from app.models.water import CropWaterProfile, FarmWaterRequirement, WaterAssessmentHistory
from app.models.weather import CurrentWeather, DailyForecast, WeatherLocation
from app.services.disease_seed import seed_disease_catalog
from app.services.water_intelligence import WaterRequirementEngine, WaterWeatherInput, water_status
from app.services.water_seed import seed_water_profiles
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
        seed_water_profiles(session)
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
                    temperature_c=Decimal("31.00"),
                    humidity_percent=Decimal("70.00"),
                    rainfall_mm=Decimal("2.00"),
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
                    rainfall_mm=Decimal("2.00"),
                    wind_speed_kmh=Decimal("10.00"),
                    pressure_hpa=Decimal("1004.00"),
                    cloud_cover_percent=Decimal("70.00"),
                ),
            ]
        )
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_requirement_calculation_deficit_logic() -> None:
    profile = CropWaterProfile(
        crop_id=1,
        stage_id=1,
        min_mm_per_day=Decimal("5.00"),
        optimal_mm_per_day=Decimal("7.00"),
        max_mm_per_day=Decimal("9.00"),
    )

    result = WaterRequirementEngine().calculate(
        profile,
        WaterWeatherInput(rainfall_mm=Decimal("2.00"), temperature_c=Decimal("31.00")),
    )

    assert result.estimated_requirement_mm == Decimal("7.70")
    assert result.rainfall_mm == Decimal("2.00")
    assert result.deficit_mm == Decimal("5.70")
    assert result.surplus_mm == Decimal("0.00")
    assert result.status == "Deficit"


def test_surplus_logic_and_status_mapping() -> None:
    profile = CropWaterProfile(
        crop_id=1,
        stage_id=1,
        min_mm_per_day=Decimal("4.00"),
        optimal_mm_per_day=Decimal("5.00"),
        max_mm_per_day=Decimal("7.00"),
    )

    result = WaterRequirementEngine().calculate(
        profile,
        WaterWeatherInput(rainfall_mm=Decimal("8.00"), temperature_c=Decimal("25.00")),
    )

    assert result.estimated_requirement_mm == Decimal("5.00")
    assert result.deficit_mm == Decimal("0.00")
    assert result.surplus_mm == Decimal("3.00")
    assert result.status == "Surplus"
    assert water_status(Decimal("0.00"), Decimal("0.00")) == "Adequate"


def test_water_intelligence_api_response_and_persistence() -> None:
    client = build_client()
    with TestingSessionLocal() as session:
        crop = session.scalar(select(Crop).where(Crop.name == "Rice"))
        assert crop is not None
        stage = session.scalar(select(CropStage).where(CropStage.crop_id == crop.id, CropStage.name == "Tillering"))
        assert stage is not None
        crop_id = crop.id
        stage_id = stage.id

    response = client.get(f"/api/v1/water-intelligence?farm_id=1&crop_id={crop_id}&crop_stage_id={stage_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["farm_id"] == 1
    assert payload["crop_name"] == "Rice"
    assert payload["crop_stage_name"] == "Tillering"
    assert payload["estimated_requirement_mm"] == "7.70"
    assert payload["rainfall_mm"] == "2.00"
    assert payload["deficit_mm"] == "5.70"
    assert payload["surplus_mm"] == "0.00"
    assert payload["status"] == "Deficit"

    with TestingSessionLocal() as session:
        requirements = session.scalars(select(FarmWaterRequirement)).all()
        history = session.scalars(select(WaterAssessmentHistory)).all()
        assert len(requirements) == 1
        assert len(history) == 1
        assert requirements[0].status == "Deficit"
        assert history[0].deficit_mm == Decimal("5.70")


def test_water_intelligence_validates_crop_stage_relationship() -> None:
    client = build_client()
    with TestingSessionLocal() as session:
        rice = session.scalar(select(Crop).where(Crop.name == "Rice"))
        wheat_stage = session.scalar(select(CropStage).join(Crop).where(Crop.name == "Wheat"))
        assert rice is not None
        assert wheat_stage is not None

    response = client.get(f"/api/v1/water-intelligence?farm_id=1&crop_id={rice.id}&crop_stage_id={wheat_stage.id}")

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
