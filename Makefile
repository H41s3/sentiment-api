.PHONY: run dev test lint test-cov lint-fix format format-check ci docker-build docker-up observability

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

format:
	uv run ruff format app/ tests/

format-check:
	uv run ruff format --check app/ tests/

ci: lint format-check test
	@echo "All checks passed."

docker-build:
	docker build -t sentiment-api .

docker-up:
	docker compose up

observability:
	docker compose -f docker-compose.yml -f docker-compose.observability.yml up

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up
