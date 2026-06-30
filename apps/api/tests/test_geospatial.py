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
from app.models.geospatial import GeoRegion
from app.models.language import Language
from app.models.location import District
from app.models.plot import Plot
from app.services.region_seed import seed_geo_regions
from app.services.spatial import boundary_bbox, boundary_contains_point, boundary_intersects, region_lookup
from app.utils.geo import GeoJSONValidationError, calculate_polygon_area, parse_geojson_polygon


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.9462, 26.8467],
            [80.9472, 26.8467],
            [80.9472, 26.8477],
            [80.9462, 26.8477],
            [80.9462, 26.8467],
        ]
    ],
}

LARGER_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.9462, 26.8467],
            [80.9482, 26.8467],
            [80.9482, 26.8487],
            [80.9462, 26.8487],
            [80.9462, 26.8467],
        ]
    ],
}

SHIFTED_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [80.9470, 26.8470],
            [80.9490, 26.8470],
            [80.9490, 26.8490],
            [80.9470, 26.8490],
            [80.9470, 26.8470],
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
        session.add_all([language, district, farmer, farm, plot])
        session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_geojson_polygon_feature_and_feature_collection_parsing() -> None:
    assert parse_geojson_polygon(POLYGON)["type"] == "Polygon"

    feature = {"type": "Feature", "geometry": POLYGON, "properties": {"name": "North Field"}}
    assert parse_geojson_polygon(feature)["coordinates"] == POLYGON["coordinates"]

    feature_collection = {"type": "FeatureCollection", "features": [feature]}
    assert parse_geojson_polygon(feature_collection)["coordinates"] == POLYGON["coordinates"]


def test_polygon_validation_rejects_unclosed_ring_and_bad_coordinate() -> None:
    with pytest.raises(GeoJSONValidationError):
        parse_geojson_polygon(
            {
                "type": "Polygon",
                "coordinates": [[[80.0, 26.0], [80.1, 26.0], [80.1, 26.1], [80.0, 26.1]]],
            }
        )

    with pytest.raises(GeoJSONValidationError):
        parse_geojson_polygon(
            {
                "type": "Polygon",
                "coordinates": [[[181.0, 26.0], [80.1, 26.0], [80.1, 26.1], [181.0, 26.0]]],
            }
        )


def test_area_calculation_returns_square_meters_hectares_and_acres() -> None:
    area = calculate_polygon_area(POLYGON["coordinates"])

    assert area.square_meters > 9_000
    assert area.hectares == pytest.approx(area.square_meters / 10_000)
    assert area.acres == pytest.approx(area.square_meters / 4_046.8564224)


def test_create_and_read_farm_and_plot_boundaries() -> None:
    client = build_client()

    farm_response = client.post("/api/v1/farm-boundaries", json={"farm_id": 1, "geometry": POLYGON})
    assert farm_response.status_code == 201
    farm_boundary = farm_response.json()
    assert farm_boundary["farm_id"] == 1
    assert farm_boundary["geometry"]["type"] == "Polygon"
    assert Decimal(farm_boundary["area_square_meters"]) > 0

    farm_get_response = client.get(f"/api/v1/farm-boundaries/{farm_boundary['id']}")
    assert farm_get_response.status_code == 200
    assert farm_get_response.json()["id"] == farm_boundary["id"]

    plot_response = client.post("/api/v1/plot-boundaries", json={"plot_id": 1, "geometry": POLYGON})
    assert plot_response.status_code == 201
    plot_boundary = plot_response.json()
    assert plot_boundary["plot_id"] == 1
    assert Decimal(plot_boundary["area_acres"]) > 0

    plot_get_response = client.get(f"/api/v1/plot-boundaries/{plot_boundary['id']}")
    assert plot_get_response.status_code == 200
    assert plot_get_response.json()["id"] == plot_boundary["id"]


def test_update_farm_and_plot_boundaries_replaces_geometry_and_area() -> None:
    client = build_client()

    farm_response = client.post("/api/v1/farm-boundaries", json={"farm_id": 1, "geometry": POLYGON})
    farm_boundary = farm_response.json()
    farm_update = client.put(
        f"/api/v1/farm-boundaries/{farm_boundary['id']}",
        json={"geometry": {"type": "Feature", "geometry": LARGER_POLYGON, "properties": {}}},
    )

    assert farm_update.status_code == 200
    updated_farm = farm_update.json()
    assert updated_farm["geometry"]["coordinates"] == LARGER_POLYGON["coordinates"]
    assert Decimal(updated_farm["area_square_meters"]) > Decimal(farm_boundary["area_square_meters"])
    assert updated_farm["updated_at"] is not None

    plot_response = client.post("/api/v1/plot-boundaries", json={"plot_id": 1, "geometry": POLYGON})
    plot_boundary = plot_response.json()
    plot_update = client.put(
        f"/api/v1/plot-boundaries/{plot_boundary['id']}",
        json={"geometry": {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": LARGER_POLYGON}]}},
    )

    assert plot_update.status_code == 200
    updated_plot = plot_update.json()
    assert updated_plot["geometry"]["coordinates"] == LARGER_POLYGON["coordinates"]
    assert Decimal(updated_plot["area_acres"]) > Decimal(plot_boundary["area_acres"])


def test_delete_boundaries_returns_404_after_hard_delete() -> None:
    client = build_client()

    farm_response = client.post("/api/v1/farm-boundaries", json={"farm_id": 1, "geometry": POLYGON})
    farm_boundary_id = farm_response.json()["id"]
    farm_delete = client.delete(f"/api/v1/farm-boundaries/{farm_boundary_id}")

    assert farm_delete.status_code == 204
    assert client.get(f"/api/v1/farm-boundaries/{farm_boundary_id}").status_code == 404
    assert client.delete("/api/v1/farm-boundaries/999").status_code == 404

    plot_response = client.post("/api/v1/plot-boundaries", json={"plot_id": 1, "geometry": POLYGON})
    plot_boundary_id = plot_response.json()["id"]
    plot_delete = client.delete(f"/api/v1/plot-boundaries/{plot_boundary_id}")

    assert plot_delete.status_code == 204
    assert client.get(f"/api/v1/plot-boundaries/{plot_boundary_id}").status_code == 404
    assert client.delete("/api/v1/plot-boundaries/999").status_code == 404


def test_list_boundaries_supports_pagination() -> None:
    client = build_client()

    first = client.post("/api/v1/farm-boundaries", json={"farm_id": 1, "geometry": POLYGON}).json()
    second = client.post("/api/v1/farm-boundaries", json={"farm_id": 1, "geometry": LARGER_POLYGON}).json()
    farm_list = client.get("/api/v1/farms/1/boundaries?offset=1&limit=1")

    assert farm_list.status_code == 200
    assert [item["id"] for item in farm_list.json()] == [second["id"]]
    assert client.get("/api/v1/farms/999/boundaries").status_code == 404

    first_plot = client.post("/api/v1/plot-boundaries", json={"plot_id": 1, "geometry": POLYGON}).json()
    second_plot = client.post("/api/v1/plot-boundaries", json={"plot_id": 1, "geometry": LARGER_POLYGON}).json()
    plot_list = client.get("/api/v1/plots/1/boundaries?offset=0&limit=1")

    assert first["farm_id"] == 1
    assert first_plot["plot_id"] == 1
    assert plot_list.status_code == 200
    assert [item["id"] for item in plot_list.json()] == [first_plot["id"]]
    assert second_plot["id"] != first_plot["id"]
    assert client.get("/api/v1/plots/999/boundaries").status_code == 404


def test_geo_regions_returns_empty_list() -> None:
    client = build_client()

    response = client.get("/api/v1/geo-regions")

    assert response.status_code == 200
    assert response.json() == []


def test_region_seeding_creates_idempotent_hierarchy() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        seed_geo_regions(session)
        seed_geo_regions(session)
        session.commit()

        regions = session.query(GeoRegion).order_by(GeoRegion.id).all()
        assert len(regions) == 5
        assert [region.region_type for region in regions] == ["country", "state", "district", "block", "village"]
        assert regions[-1].name == "Semra"
        assert regions[-1].parent_id == regions[-2].id


def test_spatial_helpers_handle_bbox_intersection_contains_and_lookup() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    assert boundary_bbox(POLYGON) == pytest.approx((80.9462, 26.8467, 80.9472, 26.8477))
    assert boundary_contains_point(POLYGON, (80.9467, 26.8470))
    assert not boundary_contains_point(POLYGON, (81.5, 27.5))
    assert boundary_intersects(POLYGON, SHIFTED_POLYGON)
    assert not boundary_intersects(POLYGON, {
        "type": "Polygon",
        "coordinates": [[[81.0, 27.0], [81.1, 27.0], [81.1, 27.1], [81.0, 27.1], [81.0, 27.0]]],
    })

    with TestingSessionLocal() as session:
        seed_geo_regions(session)
        session.commit()
        villages = region_lookup(session, (80.94, 26.97), region_type="village")

        assert len(villages) == 1
        assert villages[0].name == "Semra"
