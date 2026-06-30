from fastapi.testclient import TestClient

from app.config import settings
from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService


def _stub_client():
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    client = TestClient(app)
    return client


def test_batch_too_large_error_includes_configured_limit():
    client = _stub_client()
    try:
        response = client.post(
            "/api/v1/analyze/batch",
            json={"texts": ["hello"] * (settings.max_batch_size + 1)},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert str(settings.max_batch_size) in detail["message"]
    finally:
        app.dependency_overrides.clear()


def test_batch_too_large_error_includes_actual_size():
    client = _stub_client()
    try:
        actual_size = settings.max_batch_size + 5
        response = client.post(
            "/api/v1/analyze/batch",
            json={"texts": ["hello"] * actual_size},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert str(actual_size) in detail["message"]
    finally:
        app.dependency_overrides.clear()


def test_batch_too_large_error_type_is_batch_too_large():
    client = _stub_client()
    try:
        response = client.post(
            "/api/v1/analyze/batch",
            json={"texts": ["hello"] * (settings.max_batch_size + 1)},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "batch_too_large"
    finally:
        app.dependency_overrides.clear()


def test_batch_at_exact_limit_succeeds():
    client = _stub_client()
    try:
        response = client.post(
            "/api/v1/analyze/batch",
            json={"texts": ["hello"] * settings.max_batch_size},
        )
        assert response.status_code == 200
        assert response.json()["count"] == settings.max_batch_size
    finally:
        app.dependency_overrides.clear()
