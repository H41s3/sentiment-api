from unittest.mock import MagicMock

from app.config import settings
from app.limiter import _rate_limit_key, _storage_uri

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(api_key=None, ip="127.0.0.1"):
    """Build a minimal mock Request with the headers and client info that
    _rate_limit_key inspects.  get_remote_address reads request.client.host
    as the fallback when no API key is present.
    """
    request = MagicMock()
    request.headers.get.return_value = api_key
    request.client.host = ip
    return request


# ---------------------------------------------------------------------------
# Key-function tests — verify bucket assignment logic
# ---------------------------------------------------------------------------


def test_rate_limit_key_uses_api_key_when_present():
    request = _make_request(api_key="my-api-key")
    assert _rate_limit_key(request) == "key:my-api-key"


def test_rate_limit_key_falls_back_to_ip_when_no_key():
    request = _make_request(api_key=None, ip="1.2.3.4")
    assert _rate_limit_key(request) == "1.2.3.4"


def test_rate_limit_key_different_keys_produce_different_buckets():
    r1 = _make_request(api_key="key-a")
    r2 = _make_request(api_key="key-b")
    assert _rate_limit_key(r1) != _rate_limit_key(r2)


def test_rate_limit_key_prefix_prevents_collision_with_ip():
    # An API key whose value looks like an IP must not share a bucket
    # with real traffic from that IP address.
    r_key = _make_request(api_key="1.2.3.4")
    r_ip = _make_request(api_key=None, ip="1.2.3.4")
    assert _rate_limit_key(r_key) != _rate_limit_key(r_ip)


# ---------------------------------------------------------------------------
# Storage-backend tests — verify _storage_uri picks the right backend
# ---------------------------------------------------------------------------


def test_storage_uri_defaults_to_memory_when_redis_url_unset(monkeypatch):
    """With no REDIS_URL, the limiter should use per-process in-memory
    counters — the safe default for local dev and CI where Redis isn't
    running.
    """
    monkeypatch.setattr(settings, "redis_url", None)
    assert _storage_uri() == "memory://"


def test_storage_uri_uses_redis_url_when_set(monkeypatch):
    """When REDIS_URL is configured, the limiter should hand the URL
    straight to the limits library so all workers share one counter set.
    """
    monkeypatch.setattr(settings, "redis_url", "redis://redis:6379/0")
    assert _storage_uri() == "redis://redis:6379/0"
