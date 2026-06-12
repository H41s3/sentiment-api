.PHONY: run dev test lint test-cov lint-fix docker-build docker-up

run:
	uv run uvicorn app.main:app --reload --port 8000

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check app/ tests/

test-cov:
	uv run pytest tests/ -v --cov=app --cov-report=term-missing

lint-fix:
	uv run ruff check app/ tests/ --fix

docker-build:
	docker build -t sentiment-api .

docker-up:
	docker compose up

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up
