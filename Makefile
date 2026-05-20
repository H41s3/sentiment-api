.PHONY: run dev test lint docker-build docker-up

run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/

docker-build:
	docker build -t sentiment-api .

docker-up:
	docker compose up

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up
