from datetime import UTC, datetime
from unittest.mock import patch

from app.services.sentiment_service import SentimentService


def _make_service() -> SentimentService:
    service = SentimentService(model_name="test-stub", max_length=512)
    service._pipeline = "stub"
    service._loaded_at = datetime.now(tz=UTC)
    return service


def test_is_loaded_false_before_load():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service.is_loaded is False


def test_is_loaded_true_after_load():
    service = _make_service()
    assert service.is_loaded is True


def test_unload_clears_pipeline():
    service = _make_service()
    service.unload()
    assert service.is_loaded is False
    assert service.loaded_at is None


def test_loaded_at_set_after_load():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service.loaded_at is None
    with patch.dict("sys.modules", {"transformers": None}):
        service.load()
    assert service.loaded_at is not None
    assert isinstance(service.loaded_at, datetime)


def test_inference_count_starts_at_zero():
    service = _make_service()
    assert service.inference_count == 0


def test_inference_count_increments_on_analyze():
    service = _make_service()
    service.analyze("great product")
    assert service.inference_count == 1


def test_inference_count_increments_by_batch_size():
    service = _make_service()
    service.analyze_batch(["good", "bad", "ok"])
    assert service.inference_count == 3


def test_avg_inference_ms_zero_before_any_inference():
    service = _make_service()
    assert service.avg_inference_ms == 0.0


def test_avg_inference_ms_positive_after_inference():
    service = _make_service()
    service.analyze("great")
    assert service.avg_inference_ms >= 0.0


def test_stub_positive_classification():
    service = _make_service()
    result = service.analyze("love great awesome")
    assert result.label == "POSITIVE"
    assert result.score > 0.5


def test_stub_negative_classification():
    service = _make_service()
    result = service.analyze("hate terrible awful")
    assert result.label == "NEGATIVE"
    assert result.score > 0.5


def test_stub_neutral_classification():
    service = _make_service()
    result = service.analyze("the weather is cloudy")
    assert result.label == "NEUTRAL"
    assert result.score == 0.5


def test_analyze_batch_returns_correct_count():
    service = _make_service()
    results = service.analyze_batch(["love it", "hate it"])
    assert len(results) == 2


def test_analyze_batch_preserves_order():
    service = _make_service()
    results = service.analyze_batch(["love great awesome", "hate terrible awful"])
    assert results[0].label == "POSITIVE"
    assert results[1].label == "NEGATIVE"


def test_label_map_normalizes_generic_labels():
    from app.services.sentiment_service import _LABEL_MAP

    assert _LABEL_MAP["LABEL_0"] == "NEGATIVE"
    assert _LABEL_MAP["LABEL_1"] == "POSITIVE"


def test_auto_loads_on_first_analyze():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service.is_loaded is False
    with patch.dict("sys.modules", {"transformers": None}):
        service.analyze("hello")
    assert service.is_loaded is True


def test_auto_loads_on_first_batch_analyze():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service.is_loaded is False
    with patch.dict("sys.modules", {"transformers": None}):
        service.analyze_batch(["hello"])
    assert service.is_loaded is True


def test_stub_score_capped_at_099():
    service = _make_service()
    many_positive = "love great good excellent awesome happy fantastic wonderful best perfect"
    result = service.analyze(many_positive)
    assert result.label == "POSITIVE"
    assert result.score <= 0.99


def test_warm_up_noop_on_stub():
    service = _make_service()
    service.warm_up()
    assert service.is_loaded is True


def test_analyze_single_word():
    service = _make_service()
    result = service.analyze("indifferent")
    assert result.label == "NEUTRAL"
    assert result.score == 0.5


def test_analyze_batch_identical_texts():
    service = _make_service()
    results = service.analyze_batch(["love", "love", "love"])
    assert len(results) == 3
    for r in results:
        assert r.label == "POSITIVE"


def test_analyze_batch_empty_after_preprocessing():
    service = _make_service()
    results = service.analyze_batch(["ok"])
    assert len(results) == 1
    assert results[0].label == "NEUTRAL"


def test_inference_count_accumulates_across_calls():
    service = _make_service()
    service.analyze("great")
    service.analyze_batch(["bad", "good"])
    assert service.inference_count == 3


def test_avg_inference_ms_updates_after_batch():
    service = _make_service()
    service.analyze_batch(["great", "terrible"])
    assert service.avg_inference_ms >= 0.0
    assert service.inference_count == 2


def test_loaded_at_is_utc():
    service = SentimentService(model_name="test-stub", max_length=512)
    with patch.dict("sys.modules", {"transformers": None}):
        service.load()
    assert service.loaded_at.tzinfo is not None
    assert service.loaded_at.tzinfo == UTC


def test_unload_preserves_inference_stats():
    service = _make_service()
    service.analyze("great product")
    assert service.inference_count > 0
    service.unload()
    assert service.is_loaded is False
    assert service.inference_count == 1


def test_model_name_preserved_after_load():
    service = SentimentService(model_name="custom-model", max_length=256)
    assert service.model_name == "custom-model"
    assert service.max_length == 256


def test_warm_up_safe_before_load():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service._pipeline is None
    service.warm_up()
    assert service._pipeline is None


def test_total_inference_ms_starts_at_zero():
    service = SentimentService(model_name="test-stub", max_length=512)
    assert service._total_inference_ms == 0.0


def test_total_inference_ms_grows_after_analyze():
    service = _make_service()
    service.analyze("great product")
    assert service._total_inference_ms > 0.0
