from functools import lru_cache

from app.config import settings
from app.services.sentiment_service import SentimentService


@lru_cache(maxsize=1)
def get_sentiment_service() -> SentimentService:
    return SentimentService(model_name=settings.model_name, max_length=settings.max_length)
