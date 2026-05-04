from app.models.schemas import SentimentResult


class SentimentService:
    """Wraps a HuggingFace pipeline for sentiment classification."""

    def __init__(self, model_name: str, max_length: int = 512):
        self.model_name = model_name
        self.max_length = max_length
        self._pipeline = None  # lazy-loaded

    def load(self) -> None:
        # TODO: uncomment once transformers is installed
        # from transformers import pipeline
        # self._pipeline = pipeline("sentiment-analysis", model=self.model_name)
        raise NotImplementedError("Install transformers and uncomment load()")

    def analyze(self, text: str) -> SentimentResult:
        if self._pipeline is None:
            raise RuntimeError("Call load() before analyze()")
        # TODO: truncate text to max_length tokens before passing to pipeline
        result = self._pipeline(text)[0]
        return SentimentResult(label=result["label"], score=result["score"])
