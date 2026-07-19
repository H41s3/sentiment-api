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


def test_cache_clear_produces_new_instance():
    get_sentiment_service.cache_clear()
    first = get_sentiment_service()
    get_sentiment_service.cache_clear()
    second = get_sentiment_service()
    assert first is not second
    get_sentiment_service.cache_clear()


def test_cache_info_reports_hits_after_repeated_calls():
    get_sentiment_service.cache_clear()
    get_sentiment_service()
    get_sentiment_service()
    info = get_sentiment_service.cache_info()
    assert info.hits >= 1
    assert info.misses == 1
    get_sentiment_service.cache_clear()
