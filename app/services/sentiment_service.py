from app.models.schemas import SentimentResult
from app.utils.text import preprocess

_POSITIVE_WORDS = {"love", "great", "good", "excellent", "awesome", "happy", "fantastic", "wonderful", "best", "perfect"}
_NEGATIVE_WORDS = {"hate", "bad", "terrible", "awful", "horrible", "sad", "worst", "poor", "disgusting", "broken"}

# Some fine-tuned models return generic LABEL_N keys instead of human-readable
# sentiment names. This map keeps our API contract stable regardless of which
# underlying checkpoint is configured.
_LABEL_MAP = {"LABEL_0": "NEGATIVE", "LABEL_1": "POSITIVE"}


class SentimentService:
    """Wraps a HuggingFace pipeline for sentiment classification."""

    def __init__(self, model_name: str, max_length: int = 512):
        self.model_name = model_name
        self.max_length = max_length
        self._pipeline = None

    def load(self) -> None:
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                truncation=True,
                max_length=self.max_length,
            )
        except ImportError:
            self._pipeline = "stub"

    def warm_up(self) -> None:
        """Run one dummy inference to trigger PyTorch JIT compilation.
        The first real request otherwise pays a 2-5x latency penalty."""
        if self._pipeline is not None and self._pipeline != "stub":
            self._pipeline("warm up")

    def unload(self) -> None:
        """Release the pipeline and model weights from memory."""
        self._pipeline = None

    def analyze(self, text: str) -> SentimentResult:
        if self._pipeline is None:
            self.load()
        text = preprocess(text)
        if self._pipeline == "stub":
            return self._stub_analyze(text)
        result = self._pipeline(text)[0]
        return SentimentResult(label=_LABEL_MAP.get(result["label"], result["label"]), score=result["score"])

    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        if self._pipeline is None:
            self.load()
        preprocessed = [preprocess(t) for t in texts]
        if self._pipeline == "stub":
            return [self._stub_analyze(t) for t in preprocessed]
        results = self._pipeline(preprocessed)
        return [SentimentResult(label=_LABEL_MAP.get(r["label"], r["label"]), score=r["score"]) for r in results]

    def _stub_analyze(self, text: str) -> SentimentResult:
        words = set(text.lower().split())
        pos = len(words & _POSITIVE_WORDS)
        neg = len(words & _NEGATIVE_WORDS)
        if pos > neg:
            return SentimentResult(label="POSITIVE", score=min(0.7 + pos * 0.05, 0.99))
        if neg > pos:
            return SentimentResult(label="NEGATIVE", score=min(0.7 + neg * 0.05, 0.99))
        return SentimentResult(label="NEUTRAL", score=0.5)

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None
