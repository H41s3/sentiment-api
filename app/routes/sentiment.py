import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.dependencies import get_sentiment_service
from app.models.schemas import (
    BatchSentimentItem,
    BatchSentimentRequest,
    BatchSentimentResponse,
    ErrorResponse,
    SentimentRequest,
    SentimentResponse,
)
from app.services.sentiment_service import SentimentService

_AUTH_RESPONSES = {401: {"model": ErrorResponse}}

router = APIRouter(tags=["sentiment"])


@router.get("/health", tags=["meta"], summary="Versioned health check")
def versioned_health(service: SentimentService = Depends(get_sentiment_service)):
    return {
        "status": "ok",
        "model": service.model_name,
        "pipeline_loaded": service.is_loaded,
    }


@router.post("/analyze", response_model=SentimentResponse, responses=_AUTH_RESPONSES, summary="Analyze sentiment of a single text", dependencies=[Depends(verify_api_key)])
async def analyze_sentiment(
    request: SentimentRequest,
    service: SentimentService = Depends(get_sentiment_service),
):
    loop = asyncio.get_event_loop()
    t0 = time.perf_counter()
    result = await loop.run_in_executor(None, service.analyze, request.text)
    processing_ms = round((time.perf_counter() - t0) * 1000, 2)
    return SentimentResponse(text=request.text, sentiment=result, model=service.model_name, processing_ms=processing_ms)


@router.post("/analyze/batch", response_model=BatchSentimentResponse, responses=_AUTH_RESPONSES, summary="Analyze sentiment of multiple texts", dependencies=[Depends(verify_api_key)])
async def analyze_batch(
    request: BatchSentimentRequest,
    service: SentimentService = Depends(get_sentiment_service),
):
    if len(request.texts) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "batch_too_large",
                "message": f"Batch size {len(request.texts)} exceeds the configured maximum of {settings.max_batch_size}.",
            },
        )
    loop = asyncio.get_event_loop()
    t0 = time.perf_counter()
    sentiments = await loop.run_in_executor(None, service.analyze_batch, request.texts)
    processing_ms = round((time.perf_counter() - t0) * 1000, 2)
    items = [BatchSentimentItem(text=t, sentiment=s) for t, s in zip(request.texts, sentiments)]
    return BatchSentimentResponse(results=items, model=service.model_name, count=len(items), processing_ms=processing_ms)
