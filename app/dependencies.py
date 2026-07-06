from functools import lru_cache

from app.config import settings
from app.services.sentiment_service import SentimentService

__all__ = ["get_sentiment_service"]


@lru_cache(maxsize=1)
def get_sentiment_service() -> SentimentService:
    """Return the single shared SentimentService instance for this process.

    lru_cache turns this into a process-level singleton — model weights are
    loaded once and reused across all requests. Each gunicorn worker gets its
    own isolated cache (workers don't share memory), which is intentional:
    it gives us CPU parallelism without locks, queues, or shared state.

    In tests, FastAPI's dependency_overrides replaces this function entirely,
    so the real model is never loaded during the test suite.
    """
    return SentimentService(model_name=settings.model_name, max_length=settings.max_length)
