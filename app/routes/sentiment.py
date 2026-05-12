from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.dependencies import get_sentiment_service
from app.models.schemas import (
    BatchSentimentItem,
    BatchSentimentRequest,
    BatchSentimentResponse,
    SentimentRequest,
    SentimentResponse,
)
from app.services.sentiment_service import SentimentService

router = APIRouter(tags=["sentiment"])


@router.get("/health", tags=["meta"], summary="Versioned health check")
def versioned_health(service: SentimentService = Depends(get_sentiment_service)):
    return {
        "status": "ok",
        "model": service.model_name,
        "pipeline_loaded": service.is_loaded,
    }


@router.post("/analyze", response_model=SentimentResponse, summary="Analyze sentiment of a single text", dependencies=[Depends(verify_api_key)])
async def analyze_sentiment(
    request: SentimentRequest,
    service: SentimentService = Depends(get_sentiment_service),
):
    result = service.analyze(request.text)
    return SentimentResponse(text=request.text, sentiment=result, model=service.model_name)


@router.post("/analyze/batch", response_model=BatchSentimentResponse, summary="Analyze sentiment of multiple texts", dependencies=[Depends(verify_api_key)])
async def analyze_batch(
    request: BatchSentimentRequest,
    service: SentimentService = Depends(get_sentiment_service),
):
    sentiments = service.analyze_batch(request.texts)
    items = [BatchSentimentItem(text=t, sentiment=s) for t, s in zip(request.texts, sentiments)]
    return BatchSentimentResponse(results=items, model=service.model_name, count=len(items))
