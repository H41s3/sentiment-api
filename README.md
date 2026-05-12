# Sentiment Analysis API

A REST API for real-time text sentiment analysis built with FastAPI and HuggingFace Transformers.

## Features

- **POST /api/v1/analyze** — classify a single text as POSITIVE / NEGATIVE with a confidence score
- **POST /api/v1/analyze/batch** — classify up to 32 texts in one request
- **GET /api/v1/health** — versioned liveness probe with model status
- **GET /health** — root liveness probe for container orchestration
- Pydantic v2 request/response validation
- Request logging middleware (method, path, status, duration)
- Dockerized for easy deployment

## Tech Stack

| Layer | Library |
|---|---|
| Framework | FastAPI + Uvicorn |
| ML Model | HuggingFace Transformers (DistilBERT SST-2) |
| Validation | Pydantic v2 |
| Testing | Pytest + HTTPX |
| Container | Docker / Docker Compose |

## Quickstart

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd sentiment-api

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env template
cp .env.example .env

# 5. Run locally
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

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
pytest tests/ -v
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
│   └── test_sentiment.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_NAME` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace model ID |
| `MAX_LENGTH` | `512` | Max tokenizer length |
| `PORT` | `8000` | Uvicorn port |
| `API_KEY` | _(unset)_ | Optional API key — enforced on /analyze routes if set |

## Notes on the ML model

The default model (`distilbert-base-uncased-finetuned-sst-2-english`) is a binary classifier — it outputs only **POSITIVE** or **NEGATIVE**. There is no NEUTRAL class from this model. If `transformers` is not installed, the service falls back to a keyword-based stub that can return NEUTRAL.
