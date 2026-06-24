from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_live_health() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_health() -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_version() -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"service": "krishiai-api", "version": "0.1.0"}
