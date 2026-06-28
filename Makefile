.PHONY: help run dev test lint test-cov lint-fix format format-check ci docker-build docker-up observability

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

run: ## Start dev server with hot reload
	uv run uvicorn app.main:app --reload --port 8000

test: ## Run test suite
	uv run pytest tests/ -v

lint: ## Check code style with ruff
	uv run ruff check app/ tests/

test-cov: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=app --cov-report=term-missing

lint-fix: ## Auto-fix lint violations
	uv run ruff check app/ tests/ --fix

format: ## Format code with ruff
	uv run ruff format app/ tests/

format-check: ## Check formatting without changes
	uv run ruff format --check app/ tests/

ci: lint format-check test ## Run full CI pipeline locally
	@echo "All checks passed."

docker-build: ## Build Docker image
	docker build -t sentiment-api .

docker-up: ## Start production stack
	docker compose up

observability: ## Start stack with Prometheus and Grafana
	docker compose -f docker-compose.yml -f docker-compose.observability.yml up

dev: ## Start dev stack with hot reload
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up
