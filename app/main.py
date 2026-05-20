import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.dependencies import get_sentiment_service
from app.middleware import LoggingMiddleware
from app.routes import sentiment

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(name)s  %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_sentiment_service().load()
    yield


app = FastAPI(
    title="Sentiment Analysis API",
    version="0.1.0",
    description="REST API for text sentiment analysis using HuggingFace Transformers",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger("sentiment_api").error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "An unexpected error occurred."})


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
    return {"status": "ok", "model": settings.model_name}


@app.get("/health/live", tags=["meta"], summary="Liveness probe")
def liveness():
    """Always returns 200. Used by orchestrators to know the process is running."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["meta"], summary="Readiness probe")
def readiness():
    """Returns 200 only when the model is loaded and ready to serve traffic.
    Orchestrators should gate routing on this, not /health/live."""
    service = get_sentiment_service()
    if not service.is_loaded:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "reason": "model not loaded"},
        )
    return {"status": "ok", "model": settings.model_name}
