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


def test_readiness_503_content_type_is_json(unloaded_client):
    response = unloaded_client.get("/health/ready")
    assert response.status_code == 503
    assert "application/json" in response.headers["content-type"]


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


# --- /health/ready with loaded_at ---


def test_readiness_includes_loaded_at_when_model_ready():
    from datetime import UTC, datetime

    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    service._loaded_at = datetime.now(tz=UTC)
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        c = TestClient(app)
        response = c.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert "loaded_at" in body
        assert body["loaded_at"] is not None
    finally:
        app.dependency_overrides.clear()


def test_readiness_503_has_no_loaded_at(unloaded_client):
    response = unloaded_client.get("/health/ready")
    assert response.status_code == 503
    assert "loaded_at" not in response.json()


def test_readiness_loaded_at_is_iso8601():
    from datetime import UTC, datetime

    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    service._loaded_at = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        c = TestClient(app)
        body = c.get("/health/ready").json()
        datetime.fromisoformat(body["loaded_at"])
    finally:
        app.dependency_overrides.clear()


def test_top_level_health_includes_version():
    response = client.get("/health")
    body = response.json()
    assert "version" in body
    assert isinstance(body["version"], str)


def test_top_level_health_model_matches_config():
    from app.config import settings

    response = client.get("/health")
    assert response.json()["model"] == settings.model_name
