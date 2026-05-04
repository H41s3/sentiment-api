import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_501_until_service_wired():
    response = client.post("/api/v1/analyze", json={"text": "Great product!"})
    assert response.status_code == 501


def test_analyze_rejects_empty_text():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422


def test_analyze_rejects_text_too_long():
    response = client.post("/api/v1/analyze", json={"text": "a" * 5001})
    assert response.status_code == 422


# TODO: add integration tests once SentimentService.load() is implemented
# def test_analyze_positive():
#     response = client.post("/api/v1/analyze", json={"text": "I love this!"})
#     assert response.status_code == 200
#     body = response.json()
#     assert body["sentiment"]["label"] == "POSITIVE"
#     assert body["sentiment"]["score"] > 0.9
