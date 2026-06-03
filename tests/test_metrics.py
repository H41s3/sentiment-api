from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type_is_prometheus():
    response = client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]
