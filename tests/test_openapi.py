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


def test_openapi_sentiment_request_text_has_description():
    schema = client.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]
    text_props = schemas["SentimentRequest"]["properties"]["text"]
    assert "description" in text_props


def test_openapi_model_info_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]
    info_props = schemas["ModelInfoResponse"]["properties"]
    for field in ("model", "max_length", "max_batch_size", "version"):
        assert "description" in info_props[field], f"{field} missing description"


def test_openapi_health_endpoints_have_summaries():
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "summary" in paths["/health/live"]["get"]
    assert "summary" in paths["/health/ready"]["get"]
    assert "summary" in paths["/health"]["get"]


def test_openapi_metrics_endpoint_excluded_from_schema():
    schema = client.get("/openapi.json").json()
    assert "/metrics" not in schema["paths"]


def test_openapi_batch_endpoint_documents_401_response():
    schema = client.get("/openapi.json").json()
    post = schema["paths"]["/api/v1/analyze/batch"]["post"]
    assert "401" in post["responses"]


def test_openapi_error_response_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["ErrorResponse"]["properties"]
    assert "description" in props["error"]
    assert "description" in props["message"]


def test_openapi_sentiment_result_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["SentimentResult"]["properties"]
    assert "description" in props["label"]
    assert "description" in props["score"]


def test_openapi_schema_contains_versioned_health_path():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/health" in schema["paths"]


def test_openapi_versioned_health_has_summary():
    schema = client.get("/openapi.json").json()
    get = schema["paths"]["/api/v1/health"]["get"]
    assert "summary" in get
    assert len(get["summary"]) > 0


def test_openapi_analyze_endpoint_has_summary():
    schema = client.get("/openapi.json").json()
    post = schema["paths"]["/api/v1/analyze"]["post"]
    assert "summary" in post
    assert len(post["summary"]) > 0


def test_openapi_batch_endpoint_has_summary():
    schema = client.get("/openapi.json").json()
    post = schema["paths"]["/api/v1/analyze/batch"]["post"]
    assert "summary" in post
    assert len(post["summary"]) > 0


def test_openapi_info_endpoint_has_summary():
    schema = client.get("/openapi.json").json()
    get = schema["paths"]["/api/v1/info"]["get"]
    assert "summary" in get
    assert len(get["summary"]) > 0


def test_openapi_sentiment_response_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["SentimentResponse"]["properties"]
    for field in ("text", "sentiment", "model", "processing_ms"):
        assert "description" in props[field], f"SentimentResponse.{field} missing description"


def test_openapi_batch_sentiment_response_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["BatchSentimentResponse"]["properties"]
    for field in ("results", "model", "count", "processing_ms"):
        assert "description" in props[field], f"BatchSentimentResponse.{field} missing description"


def test_openapi_batch_sentiment_item_fields_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["BatchSentimentItem"]["properties"]
    for field in ("text", "sentiment"):
        assert "description" in props[field], f"BatchSentimentItem.{field} missing description"


def test_openapi_model_info_inference_stats_have_descriptions():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["ModelInfoResponse"]["properties"]
    for field in ("inference_count", "avg_inference_ms"):
        assert "description" in props[field], f"ModelInfoResponse.{field} missing description"


def test_openapi_analyze_endpoint_tagged_as_sentiment():
    schema = client.get("/openapi.json").json()
    tags = schema["paths"]["/api/v1/analyze"]["post"]["tags"]
    assert "sentiment" in tags


def test_openapi_info_endpoint_tagged_as_meta():
    schema = client.get("/openapi.json").json()
    tags = schema["paths"]["/api/v1/info"]["get"]["tags"]
    assert "meta" in tags


def test_openapi_error_response_fields_have_examples():
    schema = client.get("/openapi.json").json()
    props = schema["components"]["schemas"]["ErrorResponse"]["properties"]
    assert "examples" in props["error"], "ErrorResponse.error missing examples"
    assert "examples" in props["message"], "ErrorResponse.message missing examples"


def test_openapi_sentiment_request_text_has_example():
    schema = client.get("/openapi.json").json()
    text_prop = schema["components"]["schemas"]["SentimentRequest"]["properties"]["text"]
    assert "examples" in text_prop
