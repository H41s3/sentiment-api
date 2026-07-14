from fastapi.testclient import TestClient

from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService


def test_versioned_health_reports_pipeline_loaded_true():
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        client = TestClient(app)
        body = client.get("/api/v1/health").json()
        assert body["pipeline_loaded"] is True
    finally:
        app.dependency_overrides.clear()


def test_versioned_health_reports_pipeline_loaded_false():
    service = SentimentService(model_name="test-stub", max_length=512)
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        client = TestClient(app)
        body = client.get("/api/v1/health").json()
        assert body["pipeline_loaded"] is False
    finally:
        app.dependency_overrides.clear()


def test_versioned_health_model_matches_service():
    service = SentimentService(model_name="custom-model-name", max_length=256)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        client = TestClient(app)
        body = client.get("/api/v1/health").json()
        assert body["model"] == "custom-model-name"
    finally:
        app.dependency_overrides.clear()


def test_versioned_health_status_ok_regardless_of_pipeline():
    service = SentimentService(model_name="test-stub", max_length=512)
    app.dependency_overrides[get_sentiment_service] = lambda: service
    try:
        client = TestClient(app)
        body = client.get("/api/v1/health").json()
        assert body["status"] == "ok"
    finally:
        app.dependency_overrides.clear()
