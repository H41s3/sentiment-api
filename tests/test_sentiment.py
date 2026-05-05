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
    assert response.status_code == 422


def test_batch_each_item_has_shape(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["good", "bad"]})
    assert response.status_code == 200
    for item in response.json()["results"]:
        assert "text" in item
        assert "sentiment" in item
        assert "label" in item["sentiment"]
        assert "score" in item["sentiment"]
