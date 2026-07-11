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


def test_content_security_policy_header():
    response = client.get("/health/live")
    csp = response.headers["content-security-policy"]
    assert csp == "default-src 'none'; frame-ancestors 'none'"


def test_strict_transport_security_header():
    response = client.get("/health/live")
    assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"


def test_x_dns_prefetch_control_header():
    response = client.get("/health/live")
    assert response.headers["x-dns-prefetch-control"] == "off"


def test_security_headers_present_on_error_responses():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422
    assert response.headers["x-content-type-options"] == "nosniff"


def test_security_headers_present_on_health_endpoints():
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"


def test_security_headers_present_on_metrics_endpoint():
    response = client.get("/metrics")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_security_headers_present_on_404_responses():
    response = client.get("/nonexistent/path")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"


def test_security_headers_present_on_method_not_allowed():
    response = client.delete("/health/live")
    assert response.status_code == 405
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
