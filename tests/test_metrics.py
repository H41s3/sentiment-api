from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type_is_prometheus():
    response = client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


def test_metrics_contains_http_requests_metric():
    client.get("/health/live")
    response = client.get("./metrics")
    assert "http_requests_total" in response.text


def test_metrics_contains_model_loaded_gauge():
    response = client.get("/metrics")
    assert "sentiment_model_loaded" in response.text


def test_inference_counter_increments_after_analyze():
    client.post("/api/v1/analyze", json={"text": "I love this"})
    response = client.get("/metrics")
    assert "sentiment_inference_requests_total" in response.text


def test_inference_duration_histogram_present_after_analyze():
    client.post("/api/v1/analyze", json={"text": "great product"})
    response = client.get("/metrics")
    assert "sentiment_inference_duration_seconds" in response.text


def test_batch_size_histogram_present_after_batch_analyze():
    client.post("/api/v1/analyze/batch", json={"texts": ["Good", "Bad", "Okay"]})
    response = client.get("/metrics")
    assert "sentiment_batch_size" in response.text


def test_batch_size_histogram_count_increments_per_request():
    client.post("/api/v1/analyze/batch", json={"texts": ["one", "two", "three", "four", "five"]})
    response = client.get("/metrics")
    assert "sentiment_batch_size_count" in response.text
