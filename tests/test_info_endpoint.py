import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService


@pytest.fixture
def info_client():
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_info_model_matches_config(info_client):
    from app.config import settings

    body = info_client.get("/api/v1/info").json()
    assert body["model"] == settings.model_name


def test_info_max_length_matches_service(info_client):
    body = info_client.get("/api/v1/info").json()
    assert body["max_length"] == 512


def test_info_version_is_string(info_client):
    body = info_client.get("/api/v1/info").json()
    assert isinstance(body["version"], str)
    assert len(body["version"]) > 0


def test_info_inference_count_zero_initially(info_client):
    body = info_client.get("/api/v1/info").json()
    assert body["inference_count"] == 0


def test_info_avg_inference_ms_rounds_to_two_decimals(info_client):
    info_client.post("/api/v1/analyze", json={"text": "great"})
    body = info_client.get("/api/v1/info").json()
    ms = body["avg_inference_ms"]
    assert ms == round(ms, 2)


def test_info_inference_count_tracks_single_and_batch(info_client):
    info_client.post("/api/v1/analyze", json={"text": "great"})
    info_client.post("/api/v1/analyze/batch", json={"texts": ["good", "bad"]})
    body = info_client.get("/api/v1/info").json()
    assert body["inference_count"] == 3


def test_info_response_model_validates():
    from app.models.schemas import ModelInfoResponse

    data = {
        "model": "test",
        "max_length": 512,
        "max_batch_size": 32,
        "version": "0.1.0",
        "inference_count": 0,
        "avg_inference_ms": 0.0,
    }
    obj = ModelInfoResponse(**data)
    assert obj.model == "test"
