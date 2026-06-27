from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_schema_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Sentiment Analysis API"
    assert schema["info"]["version"] == "0.1.0"


def test_openapi_schema_contains_analyze_path():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/analyze" in schema["paths"]


def test_openapi_schema_contains_batch_path():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/analyze/batch" in schema["paths"]


def test_openapi_tags_have_descriptions():
    schema = client.get("/openapi.json").json()
    tags = {t["name"]: t for t in schema["tags"]}
    assert "sentiment" in tags
    assert "description" in tags["sentiment"]
    assert "meta" in tags
    assert "description" in tags["meta"]


def test_swagger_ui_available():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
