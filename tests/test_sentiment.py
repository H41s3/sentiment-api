import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --- health ---

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_versioned_health(stub_client):
    response = stub_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["pipeline_loaded"] is True


# --- single analyze ---

def test_analyze_rejects_empty_text():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422


def test_analyze_rejects_text_too_long():
    response = client.post("/api/v1/analyze", json={"text": "a" * 5001})
    assert response.status_code == 422


def test_analyze_positive(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "I love this product, it is great!"})
    assert response.status_code == 200
    body = response.json()
    assert body["sentiment"]["label"] == "POSITIVE"
    assert body["sentiment"]["score"] > 0.5


def test_analyze_negative(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "This is terrible and awful"})
    assert response.status_code == 200
    body = response.json()
    assert body["sentiment"]["label"] == "NEGATIVE"
    assert body["sentiment"]["score"] > 0.5


def test_analyze_response_shape(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "Hello world"})
    assert response.status_code == 200
    body = response.json()
    assert "text" in body
    assert "sentiment" in body
    assert "model" in body


# --- batch analyze ---

def test_batch_analyze_basic(stub_client):
    payload = {"texts": ["I love this!", "This is bad"]}
    response = stub_client.post("/api/v1/analyze/batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert len(body["results"]) == 2


def test_batch_analyze_rejects_empty_list(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": []})
    assert response.status_code == 422


def test_batch_analyze_rejects_oversized_batch(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["hello"] * 33})
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "batch_too_large"


def test_batch_each_item_has_shape(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["good", "bad"]})
    assert response.status_code == 200
    for item in response.json()["results"]:
        assert "text" in item
        assert "sentiment" in item
        assert "label" in item["sentiment"]
        assert "score" in item["sentiment"]


# --- API key auth ---

def test_analyze_no_key_when_auth_disabled(stub_client):
    """When API_KEY is not set, requests without a key should pass."""
    response = stub_client.post("/api/v1/analyze", json={"text": "I love this"})
    assert response.status_code == 200


def test_analyze_rejects_wrong_key(stub_client, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_key", "secret-key")
    response = stub_client.post(
        "/api/v1/analyze",
        json={"text": "I love this"},
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401


def test_analyze_accepts_correct_key(stub_client, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_key", "secret-key")
    response = stub_client.post(
        "/api/v1/analyze",
        json={"text": "I love this"},
        headers={"x-api-key": "secret-key"},
    )
    assert response.status_code == 200


# --- X-Request-ID header ---

def test_response_includes_request_id(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "Hello"})
    assert "x-request-id" in response.headers


def test_response_echoes_provided_request_id(stub_client):
    response = stub_client.post(
        "/api/v1/analyze",
        json={"text": "Hello"},
        headers={"x-request-id": "my-trace-id-123"},
    )
    assert response.headers["x-request-id"] == "my-trace-id-123"


# --- preprocessing ---

def test_analyze_strips_html(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "<b>I love</b> this great product"})
    assert response.status_code == 200
    assert response.json()["sentiment"]["label"] == "POSITIVE"


def test_analyze_handles_url_in_text(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "Check https://example.com it is great"})
    assert response.status_code == 200
