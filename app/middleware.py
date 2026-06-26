import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("sentiment_api")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Attaches a request ID to every request and emits a structured access log line.

    The request ID is echoed back in the X-Request-ID response header. If the
    caller provides their own ID we use it — this enables end-to-end trace
    correlation across services without a dedicated tracing backend. If they
    don't, we generate a UUID so every log line is still uniquely addressable.

    Total latency (network + serialization + inference) is logged here.
    Inference-only latency is separately tracked in the route handlers via
    processing_ms so the two can be compared to isolate where time is spent.
    """

    async def dispatch(self, request: Request, call_next):
        # Prefer caller-supplied ID so their logs and ours can be joined on the same key.
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logger.info(
            "[%s] %s %s -> %d  (%.1f ms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            ms,
        )
        response.headers["x-request-id"] = request_id
        return response
