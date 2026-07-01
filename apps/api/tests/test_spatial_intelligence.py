import json
from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.geospatial import FarmBoundary, PlotBoundary
from app.models.language import Language
from app.models.location import District
from app.models.plot import Plot
from app.services.region_seed import seed_geo_regions
from app.services.spatial_intelligence import polygon_centroid, polygon_perimeter_meters
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

PLOT_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.93, 26.96],
            [80.95, 26.96],
            [80.95, 26.98],
            [80.93, 26.98],
            [80.93, 26.96],
        ]
    ],
}

SECOND_FARM_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.94, 26.97],
            [80.98, 26.97],
            [80.98, 27.01],
            [80.94, 27.01],
            [80.94, 26.97],
        ]
    ],
}

SECOND_PLOT_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [81.15, 27.10],
            [81.18, 27.10],
            [81.18, 27.13],
            [81.15, 27.13],
            [81.15, 27.10],
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
        seed_geo_regions(session)
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
        first_farm = Farm(
            id=1,
            farmer_id=1,
            district_id=1,
            name="North Field",
            village="Semra",
            total_acreage=Decimal("2.50"),
        )
        second_farm = Farm(
            id=2,
            farmer_id=1,
            district_id=1,
            name="East Field",
            village="Semra",
            total_acreage=Decimal("3.00"),
        )
        first_plot = Plot(id=1, farm_id=1, name="Plot A", acreage=Decimal("1.25"), current_crop="Wheat")
        second_plot = Plot(id=2, farm_id=2, name="Plot B", acreage=Decimal("1.50"), current_crop="Rice")
        session.add_all([language, district, farmer, first_farm, second_farm, first_plot, second_plot])
        session.flush()
        session.add_all(
            [
                _farm_boundary(1, FARM_POLYGON),
                _farm_boundary(2, SECOND_FARM_POLYGON),
                _plot_boundary(1, PLOT_POLYGON),
                _plot_boundary(2, SECOND_PLOT_POLYGON),
            ]
        )
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_point_lookup_returns_containing_boundaries_and_regions() -> None:
    client = build_client()

    response = client.post("/api/v1/spatial/point-lookup", json={"longitude": 80.94, "latitude": 26.97})

    assert response.status_code == 200
    payload = response.json()
    assert [item["owner_id"] for item in payload["farm_boundaries"]] == [1, 2]
    assert [item["owner_id"] for item in payload["plot_boundaries"]] == [1]
    assert {region["region_type"] for region in payload["regions"]} == {
        "country",
        "state",
        "district",
        "block",
        "village",
    }


def test_nearby_search_returns_distance_sorted_results() -> None:
    client = build_client()

    response = client.post("/api/v1/spatial/nearby", json={"longitude": 80.94, "latitude": 26.97, "radius_km": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["farms"][0]["owner_id"] == 1
    assert payload["plots"][0]["owner_id"] == 1
    assert payload["farms"][0]["distance_km"] == pytest.approx(0)
    assert payload["regions"]


def test_intersections_returns_farm_farm_farm_plot_and_plot_plot_metadata() -> None:
    client = build_client()

    all_response = client.get("/api/v1/spatial/intersections")
    farm_plot_response = client.get("/api/v1/spatial/intersections?relation_type=farm/plot")

    assert all_response.status_code == 200
    relation_types = {item["relation_type"] for item in all_response.json()["intersections"]}
    assert "farm/farm" in relation_types
    assert "farm/plot" in relation_types
    assert farm_plot_response.status_code == 200
    assert all(item["relation_type"] == "farm/plot" for item in farm_plot_response.json()["intersections"])


def test_region_resolution_returns_hierarchy_for_farm_and_plot() -> None:
    client = build_client()

    farm_response = client.get("/api/v1/spatial/farm/1/regions")
    plot_response = client.get("/api/v1/spatial/plot/1/regions")

    assert farm_response.status_code == 200
    farm_regions = farm_response.json()["regions"]
    assert farm_regions["country"]["name"] == "India"
    assert farm_regions["state"]["name"] == "Uttar Pradesh"
    assert farm_regions["district"]["name"] == "Lucknow"
    assert farm_regions["block"]["name"] == "Bakshi Ka Talab"
    assert farm_regions["village"]["name"] == "Semra"
    assert plot_response.status_code == 200
    assert plot_response.json()["regions"]["village"]["name"] == "Semra"
    assert client.get("/api/v1/spatial/farm/999/regions").status_code == 404


def test_bbox_search_returns_intersecting_farms_plots_and_regions() -> None:
    client = build_client()

    response = client.post(
        "/api/v1/spatial/bbox-search",
        json={"west": 80.91, "south": 26.94, "east": 80.97, "north": 27.0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert {item["owner_id"] for item in payload["farms"]} == {1, 2}
    assert {item["owner_id"] for item in payload["plots"]} == {1}
    assert {item["region_type"] for item in payload["regions"]} >= {"country", "state", "district", "block", "village"}


def test_spatial_metrics_calculate_centroid_and_perimeter() -> None:
    centroid = polygon_centroid(FARM_POLYGON)
    perimeter = polygon_perimeter_meters(FARM_POLYGON)

    assert centroid.longitude == pytest.approx(80.94)
    assert centroid.latitude == pytest.approx(26.97)
    assert perimeter > 15_000


def _farm_boundary(farm_id: int, geometry: dict[str, object]) -> FarmBoundary:
    area = calculate_polygon_area(geometry["coordinates"])  # type: ignore[index]
    return FarmBoundary(
        farm_id=farm_id,
        geometry=json.dumps(geometry, separators=(",", ":")),
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )


def _plot_boundary(plot_id: int, geometry: dict[str, object]) -> PlotBoundary:
    area = calculate_polygon_area(geometry["coordinates"])  # type: ignore[index]
    return PlotBoundary(
        plot_id=plot_id,
        geometry=json.dumps(geometry, separators=(",", ":")),
        area_square_meters=Decimal(str(round(area.square_meters, 2))),
        area_hectares=Decimal(str(round(area.hectares, 4))),
        area_acres=Decimal(str(round(area.acres, 4))),
    )
