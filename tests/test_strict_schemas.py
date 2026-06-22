from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_rejects_extra_fields():
    response = client.post("/api/v1/analyze", json={"text": "hello", "language": "en"})
    assert response.status_code == 422


def test_batch_rejects_extra_fields():
    response = client.post(
        "/api/v1/analyze/batch", json={"texts": ["hello"], "return_all": True}
    )
    assert response.status_code == 422


def test_analyze_accepts_valid_payload():
    response = client.post("/api/v1/analyze", json={"text": "good product"})
    assert response.status_code == 200


def test_batch_accepts_valid_payload():
    response = client.post("/api/v1/analyze/batch", json={"texts": ["good", "bad"]})
    assert response.status_code == 200
