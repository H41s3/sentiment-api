from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_rejects_get_method():
    response = client.get("/api/v1/analyze")
    assert response.status_code == 405


def test_batch_analyze_rejects_get_method():
    response = client.get("/api/v1/analyze/batch")
    assert response.status_code == 405


def test_health_rejects_post_method():
    response = client.post("/health")
    assert response.status_code == 405


def test_liveness_rejects_post_method():
    response = client.post("/health/live")
    assert response.status_code == 405


def test_readiness_rejects_post_method():
    response = client.post("/health/ready")
    assert response.status_code == 405


def test_info_rejects_post_method():
    response = client.post("/api/v1/info")
    assert response.status_code == 405


def test_analyze_rejects_put_method():
    response = client.put("/api/v1/analyze", json={"text": "hello"})
    assert response.status_code == 405


def test_analyze_rejects_patch_method():
    response = client.patch("/api/v1/analyze", json={"text": "hello"})
    assert response.status_code == 405
