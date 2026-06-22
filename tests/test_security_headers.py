from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_x_content_type_options_header():
    response = client.get("/health/live")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_x_frame_options_header():
    response = client.get("/health/live")
    assert response.headers["x-frame-options"] == "DENY"


def test_referrer_policy_header():
    response = client.get("/health/live")
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_permissions_policy_header():
    response = client.get("/health/live")
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


def test_cache_control_header():
    response = client.get("/health/live")
    assert response.headers["cache-control"] == "no-store"


def test_security_headers_present_on_api_routes(stub_client):
    response = stub_client.post("/api/v1/analyze", json={"text": "hello world"})
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_security_headers_present_on_error_responses():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422
    assert response.headers["x-content-type-options"] == "nosniff"
