from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_rejects_form_encoded_body():
    response = client.post(
        "/api/v1/analyze",
        data={"text": "hello"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 422


def test_analyze_rejects_plain_text_body():
    response = client.post(
        "/api/v1/analyze",
        content="hello world",
        headers={"content-type": "text/plain"},
    )
    assert response.status_code == 422


def test_batch_rejects_form_encoded_body():
    response = client.post(
        "/api/v1/analyze/batch",
        data={"texts": "hello"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 422


def test_analyze_accepts_json_content_type():
    response = client.post(
        "/api/v1/analyze",
        json={"text": "hello world"},
    )
    assert response.status_code == 200
