.PHONY: dev test lint fmt migrate

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff check --fix .
	ruff format .

migrate:
	alembic upgrade head