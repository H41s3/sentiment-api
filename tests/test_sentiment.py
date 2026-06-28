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


def test_analyze_rejects_whitespace_only_text():
    response = client.post("/api/v1/analyze", json={"text": "   "})
    assert response.status_code == 422


def test_analyze_positive(stub_client):
    response = stub_client.post(
        "/api/v1/analyze", json={"text": "I love this product, it is great!"}
    )
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
    assert "processing_ms" in body
    assert isinstance(body["processing_ms"], float)


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


def test_batch_analyze_single_item(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["great"]})
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_batch_analyze_at_max_size(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["hello"] * 32})
    assert response.status_code == 200
    assert response.json()["count"] == 32


def test_batch_analyze_rejects_oversized_batch(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["hello"] * 33})
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "batch_too_large"


def test_batch_processing_ms_is_positive(stub_client):
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": ["good", "bad"]})
    assert response.status_code == 200
    assert response.json()["processing_ms"] >= 0.0


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


def test_generated_request_id_is_valid_uuid(stub_client):
    import uuid

    response = stub_client.post("/api/v1/analyze", json={"text": "Hello"})
    request_id = response.headers["x-request-id"]
    parsed = uuid.UUID(request_id)
    assert str(parsed) == request_id


def test_response_echoes_provided_request_id(stub_client):
    response = stub_client.post(
        "/api/v1/analyze",
        json={"text": "Hello"},
        headers={"x-request-id": "my-trace-id-123"},
    )
    assert response.headers["x-request-id"] == "my-trace-id-123"


# --- response text echo ---


def test_analyze_response_echoes_input_text(stub_client):
    input_text = "I love this product"
    response = stub_client.post("/api/v1/analyze", json={"text": input_text})
    assert response.status_code == 200
    assert response.json()["text"] == input_text


def test_batch_results_align_with_input_texts(stub_client):
    texts = ["I love this", "terrible product", "hello world"]
    response = stub_client.post("/api/v1/analyze/batch", json={"texts": texts})
    assert response.status_code == 200
    results = response.json()["results"]
    for i, item in enumerate(results):
        assert item["text"] == texts[i]


# --- preprocessing ---


def test_analyze_strips_html(stub_client):
    response = stub_client.post(
        "/api/v1/analyze", json={"text": "<b>I love</b> this great product"}
    )
    assert response.status_code == 200
    assert response.json()["sentiment"]["label"] == "POSITIVE"


def test_analyze_handles_url_in_text(stub_client):
    response = stub_client.post(
        "/api/v1/analyze", json={"text": "Check https://example.com it is great"}
    )
    assert response.status_code == 200


# --- /api/v1/info ---


def test_info_returns_200(stub_client):
    response = stub_client.get("/api/v1/info")
    assert response.status_code == 200


def test_info_response_shape(stub_client):
    body = stub_client.get("/api/v1/info").json()
    assert "model" in body
    assert "max_length" in body
    assert "max_batch_size" in body
    assert "version" in body
    assert "inference_count" in body


def test_info_inference_count_increments(stub_client):
    before = stub_client.get("/api/v1/info").json()["inference_count"]
    stub_client.post("/api/v1/analyze", json={"text": "great"})
    after = stub_client.get("/api/v1/info").json()["inference_count"]
    assert after == before + 1


def test_info_inference_count_increments_by_batch_size(stub_client):
    before = stub_client.get("/api/v1/info").json()["inference_count"]
    stub_client.post("/api/v1/analyze/batch", json={"texts": ["great", "terrible", "ok"]})
    after = stub_client.get("/api/v1/info").json()["inference_count"]
    assert after == before + 3


def test_info_max_batch_size_matches_config(stub_client):
    from app.config import settings

    body = stub_client.get("/api/v1/info").json()
    assert body["max_batch_size"] == settings.max_batch_size


# --- avg_inference_ms ---


def test_info_avg_inference_ms_in_response(stub_client):
    body = stub_client.get("/api/v1/info").json()
    assert "avg_inference_ms" in body
    assert isinstance(body["avg_inference_ms"], float)


def test_info_avg_inference_ms_is_zero_before_inference(stub_client):
    body = stub_client.get("/api/v1/info").json()
    assert body["avg_inference_ms"] == 0.0


def test_info_avg_inference_ms_positive_after_inference(stub_client):
    stub_client.post("/api/v1/analyze", json={"text": "great product"})
    body = stub_client.get("/api/v1/info").json()
    assert body["avg_inference_ms"] >= 0.0


# --- 500 error handler ---


def test_500_handler_returns_json_error(monkeypatch):
    from app.dependencies import get_sentiment_service
    from app.services import sentiment_service

    service = sentiment_service.SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service

    def boom(self, text):
        raise RuntimeError("unexpected crash")

    monkeypatch.setattr(sentiment_service.SentimentService, "analyze", boom)
    # raise_server_exceptions=False lets the global exception handler run
    # instead of re-raising the error inside the test
    error_client = TestClient(app, raise_server_exceptions=False)
    response = error_client.post("/api/v1/analyze", json={"text": "hello"})
    app.dependency_overrides.clear()
    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "internal_error"
    assert "message" in body
