import pytest
from fastapi import HTTPException

from app.auth import verify_api_key


@pytest.fixture(autouse=True)
def _enable_auth(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "api_key", "test-secret")


async def test_rejects_missing_key():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key=None)
    assert exc_info.value.status_code == 401


async def test_rejects_empty_string_key():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="")
    assert exc_info.value.status_code == 401


async def test_rejects_wrong_key():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="wrong-key")
    assert exc_info.value.status_code == 401


async def test_accepts_correct_key():
    result = await verify_api_key(x_api_key="test-secret")
    assert result is None


async def test_skips_auth_when_api_key_unset(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "api_key", None)
    result = await verify_api_key(x_api_key=None)
    assert result is None


async def test_error_response_shape():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="wrong")
    detail = exc_info.value.detail
    assert detail["error"] == "unauthorized"
    assert "message" in detail
