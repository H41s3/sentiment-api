import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def test_response_includes_x_request_id_header():
    response = client.get("/health/live")
    assert "x-request-id" in response.headers


def test_auto_generated_request_id_is_valid_uuid():
    response = client.get("/health/live")
    rid = response.headers["x-request-id"]
    assert _UUID_RE.match(rid), f"Expected UUID, got {rid!r}"


def test_caller_supplied_request_id_is_echoed_back():
    custom_id = "trace-abc-123"
    response = client.get("/health/live", headers={"x-request-id": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_each_request_gets_unique_id():
    r1 = client.get("/health/live")
    r2 = client.get("/health/live")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


def test_request_id_present_on_api_routes(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "hello world"})
    assert "x-request-id" in response.headers


def test_request_id_present_on_error_responses():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422
    assert "x-request-id" in response.headers
