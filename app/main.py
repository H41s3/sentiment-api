from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import sentiment
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: load ML model here so it's warm on first request
    yield
    # TODO: release model resources on shutdown


app = FastAPI(
    title="Sentiment Analysis API",
    version="0.1.0",
    description="REST API for text sentiment analysis using HuggingFace Transformers",
    lifespan=lifespan,
)

app.include_router(sentiment.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "model": settings.model_name}
