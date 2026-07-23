# Sentiment Analysis API

A REST API for real-time text sentiment analysis built with FastAPI and HuggingFace Transformers.

## Features

- **POST /api/v1/analyze** — classify a single text as POSITIVE / NEGATIVE with a confidence score
- **POST /api/v1/analyze/batch** — classify up to 32 texts in one request
- **GET /api/v1/health** — versioned health check with model status
- **GET /api/v1/info** — model configuration and live inference stats
- **GET /health** — legacy health check for backwards compatibility
- **GET /health/live** — liveness probe (always 200, never gates on model)
- **GET /health/ready** — readiness probe (503 until model is loaded)
- Pydantic v2 request/response validation with strict schemas
- Optional API key authentication (set `API_KEY` env var to enable)
- Per-key rate limiting (60/min single, 20/min batch)
- Security response headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Structured JSON logging with X-Request-ID tracing
- Prometheus metrics + pre-built Grafana dashboard
- Dockerized with non-root user for production deployment

## Tech Stack

| Layer | Library |
|---|---|
| Framework | FastAPI + Uvicorn + Gunicorn |
| ML Model | HuggingFace Transformers (DistilBERT SST-2) |
| Validation | Pydantic v2 |
| Auth | Optional API key (header-based) |
| Rate Limiting | SlowAPI (per-key buckets, optional Redis backend) |
| Metrics | Prometheus + Grafana |
| Linting | Ruff (check + format) |
| Testing | Pytest + pytest-cov (95% gate) |
| CI | GitHub Actions (lint, test, Docker build) |
| Container | Docker / Docker Compose |

## Quickstart

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd sentiment-api

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync --group dev

# 4. Copy env template
cp .env.example .env

# 5. Run locally
make run
```

## Docker

```bash
# Production
docker compose up --build

# Development (hot reload + source mount)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Observability

Run Prometheus + Grafana alongside the API:

```bash
make observability
```

- Grafana: http://localhost:3000 (anonymous viewer access; admin/admin for the admin account)
- Prometheus: http://localhost:9090

The "Sentiment API" dashboard is pre-provisioned and shows inference request
rate by label, p95 inference duration, batch size distribution, HTTP request
rate, and whether the model is loaded.

## Example Requests

**Single analysis:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I absolutely love this product!"}'
```

```json
{
  "text": "I absolutely love this product!",
  "sentiment": {
    "label": "POSITIVE",
    "score": 0.9998
  },
  "model": "distilbert-base-uncased-finetuned-sst-2-english"
}
```

**Batch analysis:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Great product!", "Terrible experience."]}'
```

```json
{
  "results": [
    {"text": "Great product!", "sentiment": {"label": "POSITIVE", "score": 0.9997}},
    {"text": "Terrible experience.", "sentiment": {"label": "NEGATIVE", "score": 0.9991}}
  ],
  "model": "distilbert-base-uncased-finetuned-sst-2-english",
  "count": 2
}
```

## Running Tests

```bash
make test          # run full suite
make test-cov      # run with coverage report
make lint          # ruff check
make format        # ruff format
make lint-fix      # auto-fix lint issues
```

## Project Structure

```
sentiment-api/
├── app/
│   ├── main.py                   # FastAPI app, lifespan, middleware registration
│   ├── config.py                 # Settings (env-driven via pydantic-settings)
│   ├── dependencies.py           # Singleton SentimentService factory
│   ├── middleware.py             # Request logging middleware
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   ├── routes/
│   │   └── sentiment.py          # /analyze and /analyze/batch endpoints
│   ├── services/
│   │   └── sentiment_service.py  # Model loading and inference
│   └── utils/
│       └── text.py               # Text preprocessing
├── tests/
│   ├── conftest.py               # Fixtures (client, stub_client)
│   ├── test_sentiment.py         # Endpoint and auth tests
│   ├── test_health.py            # Liveness and readiness probes
│   ├── test_metrics.py           # Prometheus metric tests
│   ├── test_config.py            # Settings validation
│   ├── test_rate_limit.py        # Rate limit key function
│   ├── test_text.py              # Text preprocessing
│   ├── test_security_headers.py  # Security header middleware
│   └── test_strict_schemas.py    # Extra field rejection
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.observability.yml
├── Makefile
└── pyproject.toml
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_NAME` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace model ID |
| `MAX_LENGTH` | `512` | Max tokenizer length (64–2048) |
| `PORT` | `8000` | Uvicorn port |
| `API_KEY` | _(unset)_ | Optional API key — enforced on /analyze routes if set |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `WEB_CONCURRENCY` | `2` | Number of gunicorn worker processes |
| `MAX_BATCH_SIZE` | `32` | Max texts per batch request (1–128) |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `REDIS_URL` | _(unset)_ | Shared rate-limit storage across workers/replicas — falls back to per-worker in-memory counters if unset |

## Notes on the ML model

The default model (`distilbert-base-uncased-finetuned-sst-2-english`) is a binary classifier — it outputs only **POSITIVE** or **NEGATIVE**. There is no NEUTRAL class from this model. If `transformers` is not installed, the service falls back to a keyword-based stub that can return NEUTRAL.
