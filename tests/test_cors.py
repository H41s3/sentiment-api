from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_allows_origin_header():
    response = client.get("/health/live", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-allow-origin"] == "*"


def test_cors_preflight_returns_200():
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200


def test_cors_preflight_allows_post():
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    allowed = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed


def test_cors_preflight_allows_get():
    response = client.options(
        "/api/v1/info",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    allowed = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allowed


def test_cors_allows_api_key_header():
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-api-key",
        },
    )
    assert response.status_code == 200
