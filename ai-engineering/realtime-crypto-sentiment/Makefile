PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help up down logs pipeline dashboard test lint clean shell healthcheck

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

up:  ## Start TimescaleDB + dashboard via docker-compose.
	docker compose up -d timescaledb

down:  ## Stop all containers.
	docker compose down

logs:  ## Tail docker logs.
	docker compose logs -f

pipeline:  ## Run the scraping + scoring + signals + paper-trader pipeline.
	$(BIN)/python -m src.pipeline

dashboard:  ## Run the Streamlit dashboard on :8501.
	$(BIN)/streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0

test:  ## Run pytest.
	$(BIN)/python scripts/run_all_tests.py

lint:  ## Run ruff.
	$(BIN)/ruff check src tests dashboard

healthcheck:  ## Print data-source + DB reachability (exit 0 if any source is healthy).
	$(BIN)/python scripts/healthcheck.py

clean:  ## Remove caches and venv.
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ .ruff_cache

shell:  ## Open a Python shell with the project's config loaded.
	$(BIN)/python -i -c "from src.config import settings; print(f'Loaded config from {settings.__class__.__name__}')"
