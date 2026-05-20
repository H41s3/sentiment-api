import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService

client = TestClient(app)


@pytest.fixture
def loaded_client():
    """Client with a stub service already marked as loaded."""
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unloaded_client():
    """Client with a service that has not been loaded yet — simulates cold start."""
    service = SentimentService(model_name="test-stub", max_length=512)
    app.dependency_overrides[get_sentiment_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- /health/live ---

def test_liveness_always_returns_200():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_does_not_depend_on_model_state(unloaded_client):
    response = unloaded_client.get("/health/live")
    assert response.status_code == 200


# --- /health/ready ---

def test_readiness_ok_when_model_loaded(loaded_client):
    response = loaded_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_503_when_model_not_loaded(unloaded_client):
    response = unloaded_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "reason" in body


# --- auth + analyze interaction ---

@pytest.fixture
def auth_client():
    """Client with stub service and API key auth enabled."""
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_analyze_blocked_without_key_when_auth_enabled(auth_client, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_key", "prod-secret")
    response = auth_client.post("/api/v1/analyze", json={"text": "great product"})
    assert response.status_code == 401


def test_analyze_passes_with_correct_key(auth_client, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_key", "prod-secret")
    response = auth_client.post(
        "/api/v1/analyze",
        json={"text": "great product"},
        headers={"x-api-key": "prod-secret"},
    )
    assert response.status_code == 200
    assert "processing_ms" in response.json()
