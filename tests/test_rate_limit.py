from unittest.mock import MagicMock

from app.limiter import _rate_limit_key


def _make_request(api_key=None, ip="127.0.0.1"):
    request = MagicMock()
    request.headers.get.return_value = api_key
