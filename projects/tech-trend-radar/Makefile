.PHONY: help up test smoke demo fetch eval report lint api clean

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

# The package lives under src/.
export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "Tech Trend Radar commands:"
	@echo "  make up     - Install dependencies into the shared venv"
	@echo "  make test   - Run the pytest suite (offline, no API key, no network)"
	@echo "  make demo   - Run the offline end-to-end demo (uses recorded snapshots)"
	@echo "  make fetch  - Fetch live data from the public APIs into data/snapshots/"
	@echo "  make eval   - Run the eval harness (burst-detection accuracy, ranking)"
	@echo "  make report - Write the trend report to reports/"
	@echo "  make api    - Run the FastAPI app on :8000"
	@echo "  make lint   - ruff check src/ tests/ scripts/"

up:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -v

smoke: demo

demo:
	$(PY) scripts/run_demo.py

fetch:
	$(PY) scripts/fetch_snapshots.py

eval:
	$(PY) -m tech_trend_radar.evaluation --out reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

report:
	$(PY) scripts/run_demo.py --report-only

api:
	$(PY) -m uvicorn app:app --port 8000

lint:
	ruff check src/ tests/ scripts/

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
