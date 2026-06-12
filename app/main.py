import logging
import sys
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.dependencies import get_sentiment_service
from app.limiter import limiter
from app.metrics import MODEL_LOADED
from app.middleware import LoggingMiddleware
from app.routes import sentiment
from app.services.sentiment_service import SentimentService

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.root.setLevel(settings.log_level.upper())
logging.root.handlers = [_handler]

_log = logging.getLogger("sentiment_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the model lifecycle tied to the application process lifetime.

    Load order matters: warm_up() must run after load() so JIT-compiled kernels
    are cached before the readiness probe starts returning 200 and traffic arrives.
    Unload runs after the yield, during graceful shutdown, to release model weights
    deterministically rather than waiting for garbage collection.
    """
    _log.info(
        "Starting Sentiment API — model=%s  max_length=%d  auth=%s  workers=%d  max_batch=%d",
        settings.model_name,
        settings.max_length,
        "enabled" if settings.api_key else "disabled",
        settings.web_concurrency,
        settings.max_batch_size,
    )
    service = get_sentiment_service()
    service.load()
    MODEL_LOADED.set(1)
    service.warm_up()
    yield
    service.unload()
    MODEL_LOADED.set(0)
    _log.info("Sentiment API shut down — model weights released")


app = FastAPI(
    title="Sentiment Analysis API",
    version="0.1.0",
    description="REST API for text sentiment analysis using HuggingFace Transformers",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log with exc_info=True so the full traceback appears in structured logs,
    # but return a generic message to the client — never leak stack traces or
    # internal paths to callers.
    _log.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred."},
    )


# Middleware is applied in reverse registration order (last registered = outermost).
# LoggingMiddleware wraps everything so it captures the true end-to-end latency
# including CORS processing time.
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(sentiment.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health_check():
    """Top-level health check kept for backwards compatibility."""
    return {"status": "ok", "model": settings.model_name, "version": app.version}


@app.get("/health/live", tags=["meta"], summary="Liveness probe")
def liveness():
    """Always returns 200. Tells orchestrators the process is running.

    This endpoint must never fail — even if the model is not loaded yet.
    Orchestrators restart containers that fail liveness, which would create
    a restart loop on slow model downloads.
    """
    return {"status": "ok"}


@app.get("/health/ready", tags=["meta"], summary="Readiness probe")
def readiness(service: SentimentService = Depends(get_sentiment_service)):
    """Returns 200 only when the model is loaded and ready to serve traffic.

    Orchestrators should gate traffic routing on this endpoint, not /health/live.
    During a cold start or deploy, this returns 503 until load() and warm_up()
    complete, preventing the first real requests from hitting an unprimed model.
    """
    if not service.is_loaded:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "reason": "model not loaded"},
        )
    return {
        "status": "ok",
        "model": settings.model_name,
        "loaded_at": service.loaded_at.isoformat() if service.loaded_at else None,
    }
