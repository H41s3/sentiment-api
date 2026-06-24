from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def _rate_limit_key(request: Request) -> str:
    """Derive a rate-limit bucket key from the inbound request.

    Authenticated requests are bucketed by API key so each consumer gets an
    independent quota. Unauthenticated traffic falls back to client IP.
    The "key:" prefix is a deliberate collision guard — without it, an API
    key whose value happens to be an IP address (e.g. "1.2.3.4") would
    silently merge with that IP's counter.
    """
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key:{api_key}"
    return get_remote_address(request)


def _storage_uri() -> str:
    """Pick the limits storage backend for the rate limiter.

    Returns "memory://" (per-process counters) when REDIS_URL is unset —
    zero config needed for local dev and the test suite. When REDIS_URL is
    set, all gunicorn workers and replicas share one set of counters via
    Redis, fixing the multi-worker rate-limit drift bug.
    """
    return settings.redis_url or "memory://"


# storage_uri is resolved once at import time; the `limits` library opens
# the connection lazily on first rate-limit check, not here.
limiter = Limiter(key_func=_rate_limit_key, storage_uri=_storage_uri())
