from prometheus_client import Counter, Gauge, Histogram

__all__ = [
    "BATCH_SIZE",
    "INFERENCE_DURATION_SECONDS",
    "INFERENCE_REQUESTS_TOTAL",
    "MODEL_LOADED",
]

INFERENCE_REQUESTS_TOTAL = Counter(
    "sentiment_inference_requests_total",
    "Total number of texts classified",
    ["endpoint", "label"],
)

INFERENCE_DURATION_SECONDS = Histogram(
    "sentiment_inference_duration_seconds",
    "Inference wall-clock time in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

MODEL_LOADED = Gauge(
    "sentiment_model_loaded",
    "1 when the pipeline is loaded and ready, 0 otherwise",
)
BATCH_SIZE = Histogram(
    "sentiment_batch_size",
    "Number of texts submitted per batch request",
    buckets=[1, 2, 5, 10, 25, 50, 100],
)
