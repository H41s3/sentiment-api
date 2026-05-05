from fastapi import APIRouter, Depends

from app.dependencies import get_sentiment_service
from app.models.schemas import SentimentRequest, SentimentResponse
from app.services.sentiment_service import SentimentService

router = APIRouter(tags=["sentiment"])


@router.post("/analyze", response_model=SentimentResponse, summary="Analyze sentiment of text")
async def analyze_sentiment(
    request: SentimentRequest,
    service: SentimentService = Depends(get_sentiment_service),
):
    result = service.analyze(request.text)
    return SentimentResponse(text=request.text, sentiment=result, model=service.model_name)
