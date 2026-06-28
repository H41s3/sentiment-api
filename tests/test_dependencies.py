from app.dependencies import get_sentiment_service


def test_get_sentiment_service_returns_same_instance():
    get_sentiment_service.cache_clear()
    first = get_sentiment_service()
    second = get_sentiment_service()
    assert first is second
    get_sentiment_service.cache_clear()


def test_get_sentiment_service_uses_configured_model():
    from app.config import settings

    get_sentiment_service.cache_clear()
    service = get_sentiment_service()
    assert service.model_name == settings.model_name
    assert service.max_length == settings.max_length
    get_sentiment_service.cache_clear()


def test_get_sentiment_service_starts_unloaded():
    get_sentiment_service.cache_clear()
    service = get_sentiment_service()
    assert service.is_loaded is False
    get_sentiment_service.cache_clear()
