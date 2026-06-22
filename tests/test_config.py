import pytest

from app.config import Settings


def test_default_settings_are_valid():
    s = Settings()
    assert s.model_name == "distilbert-base-uncased-finetuned-sst-2-english"
    assert s.max_length == 512
    assert s.max_batch_size == 32


def test_rejects_max_length_too_low():
    with pytest.raises(ValueError, match="MAX_LENGTH"):
        Settings(max_length=10)


def test_rejects_max_length_too_high():
    with pytest.raises(ValueError, match="MAX_LENGTH"):
        Settings(max_length=5000)


def test_rejects_zero_workers():
    with pytest.raises(ValueError, match="WEB_CONCURRENCY"):
        Settings(web_concurrency=0)


def test_rejects_batch_size_too_large():
    with pytest.raises(ValueError, match="MAX_BATCH_SIZE"):
        Settings(max_batch_size=200)


def test_rejects_batch_size_zero():
    with pytest.raises(ValueError, match="MAX_BATCH_SIZE"):
        Settings(max_batch_size=0)


def test_rejects_invalid_log_level():
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings(log_level="VERBOSE")


def test_accepts_debug_log_level():
    s = Settings(log_level="DEBUG")
    assert s.log_level == "DEBUG"


def test_auth_disabled_by_default():
    s = Settings()
    assert s.api_key is None
