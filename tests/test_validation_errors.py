from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_422_response_is_json():
    response = client.post("/api/v1/analyze", json={"text": ""})
    assert response.status_code == 422
    assert "application/json" in response.headers["content-type"]


def test_422_body_has_detail_key():
    response = client.post("/api/v1/analyze", json={"text": ""})
    body = response.json()
    assert "detail" in body


def test_422_detail_is_list_of_error_objects():
    response = client.post("/api/v1/analyze", json={})
    body = response.json()
    assert isinstance(body["detail"], list)
    assert len(body["detail"]) > 0
    error = body["detail"][0]
    assert "type" in error
    assert "loc" in error
    assert "msg" in error


def test_422_error_loc_identifies_field():
    response = client.post("/api/v1/analyze", json={"text": ""})
    body = response.json()
    locs = [e["loc"] for e in body["detail"]]
    field_names = [loc[-1] for loc in locs]
    assert "text" in field_names


def test_batch_422_identifies_invalid_item_index():
    response = client.post(
        "/api/v1/analyze/batch",
        json={"texts": ["valid text", ""]},
    )
    assert response.status_code == 422
    body = response.json()
    locs = [tuple(e["loc"]) for e in body["detail"]]
    has_index = any(isinstance(part, int) for loc in locs for part in loc)
    assert has_index


def test_extra_field_error_type_is_extra_forbidden():
    response = client.post(
        "/api/v1/analyze",
        json={"text": "hello", "extra": "not allowed"},
    )
    assert response.status_code == 422
    types = [e["type"] for e in response.json()["detail"]]
    assert "extra_forbidden" in types
