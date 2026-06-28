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


def test_openapi_schema_contains_info_path():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/info" in schema["paths"]


def test_openapi_analyze_documents_401_response():
    schema = client.get("/openapi.json").json()
    post = schema["paths"]["/api/v1/analyze"]["post"]
    assert "401" in post["responses"]


def test_openapi_schema_contains_error_response_model():
    schema = client.get("/openapi.json").json()
    schemas = schema.get("components", {}).get("schemas", {})
    assert "ErrorResponse" in schemas
    props = schemas["ErrorResponse"]["properties"]
    assert "error" in props
    assert "message" in props


def test_redoc_available():
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
