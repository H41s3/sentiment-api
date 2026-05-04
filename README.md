# Sentiment Analysis API

A REST API for real-time text sentiment analysis built with FastAPI and HuggingFace Transformers.

## Features

- **POST /api/v1/analyze** — classify text as positive, negative, or neutral with a confidence score
- **GET /health** — liveness probe for container orchestration
- Pydantic v2 request/response validation
- Dockerized for easy deployment

## Tech Stack

| Layer | Library |
|---|---|
| Framework | FastAPI + Uvicorn |
| ML Model | HuggingFace Transformers (DistilBERT) |
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

## Example Request

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

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
sentiment-api/
├── app/
│   ├── main.py               # FastAPI app and lifespan
│   ├── config.py             # Settings (env-driven)
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response models
│   ├── routes/
│   │   └── sentiment.py      # /analyze endpoint
│   └── services/
│       └── sentiment_service.py  # Model loading and inference
├── tests/
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
