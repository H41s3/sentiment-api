FROM python:3.12-slim

LABEL org.opencontainers.image.title="sentiment-api" \
      org.opencontainers.image.description="REST API for text sentiment analysis" \
      org.opencontainers.image.source="https://github.com/H41s3/sentiment-api" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv

WORKDIR /app

RUN groupadd --system appuser && useradd --system --gid appuser appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY --chown=appuser:appuser . .

# Pre-download model weights so first request isn't slow
RUN uv run python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')" || true

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')" || exit 1

CMD ["uv", "run", "gunicorn", "app.main:app", "-c", "gunicorn.conf.py", "--bind", "0.0.0.0:8000"]
