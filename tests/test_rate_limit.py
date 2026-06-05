from unittest.mock import MagicMock

from app.limiter import _rate_limit_key


def _make_request(api_key=None, ip="127.0.0.1"):
    request = MagicMock()
    request.headers.get.return_value = api_key
    request.client.host = ip  # used by get_remote_address as the fallback
    return request


def test_rate_limit_key_uses_api_key_when_present():
    request = _make_request(api_key="my-api-key")
    assert _rate_limit_key(request) == "key:my-api-key"
