.DEFAULT_GOAL := help
.PHONY: help run dev test test-one lint test-cov lint-fix format format-check ci clean docker-build docker-up docker-down observability check

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

run: ## Start dev server with hot reload
	uv run uvicorn app.main:app --reload --port 8000

test: ## Run test suite
	uv run pytest tests/ -v

test-one: ## Run a single test file: make test-one F=test_metrics
	uv run pytest tests/$(F).py -v

lint: ## Check code style with ruff
	uv run ruff check app/ tests/

test-cov: ## Run tests with coverage report
	uv run pytest tests/ -v --cov=app --cov-fail-under=95 --cov-report=term-missing

lint-fix: ## Auto-fix lint violations
	uv run ruff check app/ tests/ --fix

format: ## Format code with ruff
	uv run ruff format app/ tests/

format-check: ## Check formatting without changes
	uv run ruff format --check app/ tests/

ci: lint format-check test ## Run full CI pipeline locally
	@echo "All checks passed."

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage dist build *.egg-info

docker-build: ## Build Docker image
	docker build -t sentiment-api .

docker-up: ## Start production stack
	docker compose up

docker-down: ## Stop and remove all containers, networks, and volumes
	docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.observability.yml down -v

observability: ## Start stack with Prometheus and Grafana
	docker compose -f docker-compose.yml -f docker-compose.observability.yml up

dev: ## Start dev stack with hot reload
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

check: lint format-check test-cov ## Run lint, format check, and tests with coverage
