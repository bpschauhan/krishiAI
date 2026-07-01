import json
from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.weather import get_weather_service
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.geospatial import FarmBoundary
from app.models.language import Language
from app.models.location import District
from app.models.plot import Plot
from app.services.weather_cache import WeatherCache
from app.services.weather_provider import (
    CurrentWeatherData,
    DailyForecastData,
    HourlyForecastData,
    OpenMeteoProvider,
    WeatherObservationData,
    WeatherProvider,
)
from app.services.weather_service import WeatherService
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


class FakeWeatherProvider(WeatherProvider):
    name = "fake-weather"

    def __init__(self) -> None:
        self.current_calls = 0

    def current_weather(self, latitude: float, longitude: float) -> CurrentWeatherData:
        self.current_calls += 1
        return CurrentWeatherData(
            observed_at=datetime(2026, 7, 1, 6, tzinfo=timezone.utc),
            temperature_c=Decimal("31.5"),
            humidity_percent=Decimal("72"),
            rainfall_mm=Decimal("1.2"),
            wind_speed_kmh=Decimal("9.5"),
            pressure_hpa=Decimal("1005.8"),
            cloud_cover_percent=Decimal("60"),
        )

    def hourly_forecast(self, latitude: float, longitude: float, hours: int = 24) -> list[HourlyForecastData]:
        return [
            HourlyForecastData(
                forecast_time=datetime(2026, 7, 1, 7, tzinfo=timezone.utc),
                temperature_c=Decimal("32"),
                humidity_percent=Decimal("70"),
                rainfall_mm=Decimal("0.5"),
                wind_speed_kmh=Decimal("10"),
                pressure_hpa=Decimal("1004"),
                cloud_cover_percent=Decimal("55"),
            )
        ][:hours]

    def daily_forecast(self, latitude: float, longitude: float, days: int = 7) -> list[DailyForecastData]:
        return [
            DailyForecastData(
                forecast_date=date(2026, 7, 1),
                temperature_min_c=Decimal("25"),
                temperature_max_c=Decimal("34"),
                humidity_percent=None,
                rainfall_mm=Decimal("3"),
                wind_speed_kmh=Decimal("12"),
                pressure_hpa=None,
                cloud_cover_percent=None,
            )
        ][:days]

    def historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherObservationData]:
        return [
            WeatherObservationData(
                observed_at=datetime(2026, 6, 30, 6, tzinfo=timezone.utc),
                temperature_c=Decimal("30"),
                humidity_percent=Decimal("74"),
                rainfall_mm=Decimal("2"),
                wind_speed_kmh=Decimal("8"),
                pressure_hpa=Decimal("1006"),
                cloud_cover_percent=Decimal("68"),
            )
        ]


class StaticOpenMeteoProvider(OpenMeteoProvider):
    def _get_json(self, url: str, params: dict[str, object]):
        if "current" in params:
            return {
                "current": {
                    "time": "2026-07-01T06:00",
                    "temperature_2m": 31.5,
                    "relative_humidity_2m": 72,
                    "rain": 1.2,
                    "wind_speed_10m": 9.5,
                    "surface_pressure": 1005.8,
                    "cloud_cover": 60,
                }
            }
        if "daily" in params:
            return {
                "daily": {
                    "time": ["2026-07-01"],
                    "temperature_2m_min": [25],
                    "temperature_2m_max": [34],
                    "rain_sum": [3],
                    "wind_speed_10m_max": [12],
                }
            }
        return {
            "hourly": {
                "time": ["2026-07-01T07:00"],
                "temperature_2m": [32],
                "relative_humidity_2m": [70],
                "rain": [0.5],
                "wind_speed_10m": [10],
                "surface_pressure": [1004],
                "cloud_cover": [55],
            }
        }


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_client(provider: FakeWeatherProvider | None = None) -> TestClient:
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
        plot = Plot(id=1, farm_id=1, name="Plot A", acreage=Decimal("1.25"), current_crop="Wheat")
        session.add_all([language, district, farmer, farm, plot, _farm_boundary(1)])
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_weather_service] = lambda: WeatherService(provider or FakeWeatherProvider(), WeatherCache(ttl_seconds=30))
    return TestClient(app)


def test_open_meteo_provider_parses_current_hourly_daily_and_history() -> None:
    provider = StaticOpenMeteoProvider()

    current = provider.current_weather(26.97, 80.94)
    hourly = provider.hourly_forecast(26.97, 80.94, hours=1)
    daily = provider.daily_forecast(26.97, 80.94, days=1)
    history = provider.historical_weather(26.97, 80.94, date(2026, 6, 30), date(2026, 6, 30))

    assert current.temperature_c == Decimal("31.5")
    assert hourly[0].humidity_percent == Decimal("70")
    assert daily[0].temperature_max_c == Decimal("34")
    assert history[0].rainfall_mm == Decimal("0.5")


def test_farm_weather_lookup_uses_farm_boundary_centroid() -> None:
    provider = FakeWeatherProvider()
    client = build_client(provider)

    response = client.get("/api/v1/weather/current?farm_id=1")

    assert response.status_code == 200
    payload = response.json()["current"]
    assert payload["location"]["farm_id"] == 1
    assert payload["location"]["latitude"] == "26.970000"
    assert payload["location"]["longitude"] == "80.940000"
    assert payload["temperature_c"] == "31.50"


def test_hourly_daily_and_history_routes_return_provider_data() -> None:
    client = build_client()

    hourly = client.get("/api/v1/weather/hourly?farm_id=1&hours=1")
    daily = client.get("/api/v1/weather/daily?farm_id=1&days=1")
    history = client.get("/api/v1/weather/history?farm_id=1&start_date=2026-06-30&end_date=2026-06-30")

    assert hourly.status_code == 200
    assert hourly.json()["hourly"][0]["forecast_time"] == "2026-07-01T07:00:00Z"
    assert daily.status_code == 200
    assert daily.json()["daily"][0]["forecast_date"] == "2026-07-01"
    assert history.status_code == 200
    assert history.json()["observations"][0]["observed_at"] == "2026-06-30T06:00:00Z"


def test_weather_cache_uses_memory_fallback() -> None:
    cache = WeatherCache(ttl_seconds=30)
    cache._redis_client = None

    cache.set_json("weather:test", {"ok": True})

    assert cache.get_json("weather:test") == {"ok": True}


def test_service_uses_cache_for_current_weather() -> None:
    provider = FakeWeatherProvider()
    cache = WeatherCache(ttl_seconds=30)
    cache._redis_client = None
    service = WeatherService(provider, cache)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        language = Language(id=1, code="hi", name="Hindi", is_active=True)
        district = District(id=1, name="Lucknow", state="Uttar Pradesh", is_active=True)
        farmer = Farmer(id=1, full_name="Ramesh Kumar", phone_number="9876543210", village="Semra", district_id=1, language_id=1)
        farm = Farm(id=1, farmer_id=1, district_id=1, name="North Field", village="Semra", total_acreage=Decimal("2.50"))
        session.add_all([language, district, farmer, farm, _farm_boundary(1)])
        session.commit()

        service.current_weather(session, service_query(1))
        service.current_weather(session, service_query(1))

    assert provider.current_calls == 1


def service_query(farm_id: int):
    from app.schemas.weather import WeatherQuery

    return WeatherQuery(farm_id=farm_id)


def _farm_boundary(farm_id: int) -> FarmBoundary:
    area = calculate_polygon_area(FARM_POLYGON["coordinates"])
    return FarmBoundary(
        farm_id=farm_id,
        geometry=json.dumps(FARM_POLYGON, separators=(",", ":")),
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
