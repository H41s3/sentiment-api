from fastapi import APIRouter, HTTPException

from app.models.schemas import SentimentRequest, SentimentResponse

router = APIRouter(tags=["sentiment"])


@router.post("/analyze", response_model=SentimentResponse, summary="Analyze sentiment of text")
async def analyze_sentiment(request: SentimentRequest):
    # TODO: inject SentimentService and call .analyze(request.text)
    raise HTTPException(status_code=501, detail="Sentiment service not wired up yet")
