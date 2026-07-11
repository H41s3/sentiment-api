from fastapi.testclient import TestClient

from app.dependencies import get_sentiment_service
from app.main import app
from app.services.sentiment_service import SentimentService


def _crash_client(monkeypatch):
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    app.dependency_overrides[get_sentiment_service] = lambda: service

    def boom(self, text):
        raise RuntimeError("unexpected crash")

    monkeypatch.setattr(SentimentService, "analyze", boom)
    return TestClient(app, raise_server_exceptions=False)


def test_500_does_not_leak_traceback(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert response.status_code == 500
        body = response.json()
        assert "traceback" not in body
        assert "Traceback" not in response.text
        assert "RuntimeError" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_500_returns_generic_message(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert response.status_code == 500
        body = response.json()
        assert body["message"] == "An unexpected error occurred."
    finally:
        app.dependency_overrides.clear()


def test_500_has_error_key(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        body = response.json()
        assert body["error"] == "internal_error"
    finally:
        app.dependency_overrides.clear()


def test_500_content_type_is_json(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert "application/json" in response.headers["content-type"]
    finally:
        app.dependency_overrides.clear()


def test_500_does_not_include_file_paths(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert response.status_code == 500
        assert "/app/" not in response.text
        assert "sentiment_service.py" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_500_does_not_leak_exception_class_name(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert response.status_code == 500
        body = response.json()
        assert "RuntimeError" not in body.get("message", "")
        assert "unexpected crash" not in body.get("message", "")
    finally:
        app.dependency_overrides.clear()


def test_500_does_not_leak_module_names(monkeypatch):
    client = _crash_client(monkeypatch)
    try:
        response = client.post("/api/v1/analyze", json={"text": "hello"})
        assert response.status_code == 500
        assert "app.services" not in response.text
        assert "app.routes" not in response.text
    finally:
        app.dependency_overrides.clear()
