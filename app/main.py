import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.add_middleware(LoggingMiddleware)
app.include_router(sentiment.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "model": settings.model_name}
