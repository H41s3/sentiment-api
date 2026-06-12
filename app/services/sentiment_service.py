import time
from datetime import datetime, timezone

from app.models.schemas import SentimentResult
from app.utils.text import preprocess

_POSITIVE_WORDS = {
    "love",
    "great",
    "good",
    "excellent",
    "awesome",
    "happy",
    "fantastic",
    "wonderful",
    "best",
    "perfect",
}
_NEGATIVE_WORDS = {
    "hate",
    "bad",
    "terrible",
    "awful",
    "horrible",
    "sad",
    "worst",
    "poor",
    "disgusting",
    "broken",
}

# Some fine-tuned checkpoints emit generic LABEL_0/LABEL_1 instead of human-readable
# sentiment names. This map normalizes them at the service layer so the API
# contract stays stable regardless of which model is configured via MODEL_NAME.
_LABEL_MAP = {"LABEL_0": "NEGATIVE", "LABEL_1": "POSITIVE"}


class SentimentService:
    """Wraps a HuggingFace pipeline for sentiment classification.

    The pipeline is intentionally not loaded at construction time. Call load()
    during application startup so the lifespan hook controls load order and the
    readiness probe stays false until the model is ready to serve traffic.

    Falls back to a keyword-matching stub when the transformers package is not
    installed. This keeps the test suite and CI fast — no 260MB model download
    required to run tests.
    """

    def __init__(self, model_name: str, max_length: int = 512):
        self.model_name = model_name
        self.max_length = max_length
        self._pipeline = None
        self._inference_count: int = 0
        self._total_inference_ms: float = 0.0
        self._loaded_at: datetime | None = None

    def load(self) -> None:
        """Download (or load from local cache) the model weights and initialize the pipeline."""
        try:
            from transformers import pipeline

            self._pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                # Let the tokenizer truncate at the correct subword boundary rather
                # than slicing the raw string at an arbitrary character offset.
                truncation=True,
                max_length=self.max_length,
            )
        except ImportError:
            # transformers not installed — fall back to the keyword stub so
            # lightweight deployments and the test suite work without ML deps.
            self._pipeline = "stub"
        self._loaded_at = datetime.now(tz=timezone.utc)

    def warm_up(self) -> None:
        """Run one dummy inference to trigger PyTorch JIT kernel compilation.

        The first real forward pass is 2-5x slower than subsequent ones while
        PyTorch compiles and caches CUDA/CPU kernels. Running this during startup
        absorbs that penalty before the readiness probe opens traffic to the pod.
        """
        if self._pipeline is not None and self._pipeline != "stub":
            self._pipeline("warm up")

    def unload(self) -> None:
        """Release the pipeline and model weights from memory.

        Called during application shutdown. Without an explicit release, PyTorch
        tensors stay referenced until GC decides to reclaim them — on GPU this
        means VRAM stays occupied until the driver releases the CUDA context.
        """
        self._pipeline = None
        self._loaded_at = None

    def analyze(self, text: str) -> SentimentResult:
        """Preprocess and classify a single text string.

        This method is synchronous and blocks for the duration of the forward
        pass. Always call it via run_in_executor from async route handlers so
        the event loop stays free to accept new connections during inference.
        """
        if self._pipeline is None:
            self.load()
        text = preprocess(text)
        _t0 = time.perf_counter()
        if self._pipeline == "stub":
            result = self._stub_analyze(text)
        else:
            raw = self._pipeline(text)[0]
            result = SentimentResult(
                label=_LABEL_MAP.get(raw["label"], raw["label"]),
                score=raw["score"],
            )
        self._inference_count += 1
        self._total_inference_ms += (time.perf_counter() - _t0) * 1000
        return result

    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        """Preprocess and classify a list of texts in a single forward pass.

        HuggingFace pipelines accept a list natively and execute one batched
        matrix multiplication. This is dramatically faster than calling analyze()
        in a loop — on GPU it fully utilizes tensor cores instead of serializing
        N separate kernel launches.
        """
        if self._pipeline is None:
            self.load()
        preprocessed = [preprocess(t) for t in texts]
        _t0 = time.perf_counter()
        if self._pipeline == "stub":
            items = [self._stub_analyze(t) for t in preprocessed]
        else:
            items = [
                SentimentResult(
                    label=_LABEL_MAP.get(r["label"], r["label"]),
                    score=r["score"],
                )
                for r in self._pipeline(preprocessed)
            ]
        self._inference_count += len(items)
        self._total_inference_ms += (time.perf_counter() - _t0) * 1000
        return items

    def _stub_analyze(self, text: str) -> SentimentResult:
        """Keyword-based fallback used when the real pipeline is unavailable.

        Intentionally simple — this exists for dev and testing only. It should
        never be the primary path in a production deployment.
        """
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

    @property
    def inference_count(self) -> int:
        return self._inference_count

    @property
    def loaded_at(self) -> datetime | None:
        return self._loaded_at

    @property
    def avg_inference_ms(self) -> float:
        if self._inference_count == 0:
            return 0.0
        return round(self._total_inference_ms / self._inference_count, 2)
