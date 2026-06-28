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


# ---------------------------------------------------------------------------
# Redis URL — opt-in shared storage for the rate limiter
# ---------------------------------------------------------------------------


def test_redis_url_disabled_by_default():
    """REDIS_URL should be None out of the box so local dev and CI don't
    need a running Redis instance — the limiter falls back to per-process
    in-memory counters automatically.
    """
    s = Settings()
    assert s.redis_url is None


def test_redis_url_accepts_valid_redis_string():
    """When explicitly set, the raw URL string should pass through to the
    limiter unchanged — no transformation or validation beyond Pydantic's
    type coercion.
    """
    s = Settings(redis_url="redis://redis:6379/0")
    assert s.redis_url == "redis://redis:6379/0"


# ---------------------------------------------------------------------------
# Boundary-valid edge cases — values at the exact limits of valid ranges
# ---------------------------------------------------------------------------


def test_accepts_min_valid_max_length():
    s = Settings(max_length=64)
    assert s.max_length == 64


def test_accepts_max_valid_max_length():
    s = Settings(max_length=2048)
    assert s.max_length == 2048


def test_accepts_min_valid_batch_size():
    s = Settings(max_batch_size=1)
    assert s.max_batch_size == 1


def test_accepts_max_valid_batch_size():
    s = Settings(max_batch_size=128)
    assert s.max_batch_size == 128


def test_accepts_single_worker():
    s = Settings(web_concurrency=1)
    assert s.web_concurrency == 1


def test_accepts_case_insensitive_log_level():
    s = Settings(log_level="debug")
    assert s.log_level == "debug"


def test_rejects_max_length_just_below_minimum():
    with pytest.raises(ValueError, match="MAX_LENGTH"):
        Settings(max_length=63)


def test_rejects_max_length_just_above_maximum():
    with pytest.raises(ValueError, match="MAX_LENGTH"):
        Settings(max_length=2049)
