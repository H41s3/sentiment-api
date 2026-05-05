import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def stub_client():
    """Client with stub pipeline pre-loaded — no transformers needed."""
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
