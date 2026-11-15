.PHONY: help up test smoke demo eval report lint api

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

# The package lives under src/, and the trade-finder modules it imports live
# in a sibling project. Both need to be importable.
export PYTHONPATH := $(CURDIR)/src:$(CURDIR)/../realtime-stock-pipeline/trade-finder:$(PYTHONPATH)

help:
	@echo "Trade-Sourcing AI commands:"
	@echo "  make up     - Install dependencies into the shared venv"
	@echo "  make test   - Run the pytest suite (offline, no API key)"
	@echo "  make demo   - Run the offline end-to-end sourcing demo"
	@echo "  make eval   - Run the eval harness (recall@k, nDCG, decision accuracy)"
	@echo "  make report - Write the value report to reports/"
	@echo "  make api    - Run the FastAPI app on :8000"
	@echo "  make lint   - ruff check src/ tests/"

up:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -v

smoke: demo

demo:
	$(PY) scripts/run_demo.py

eval:
	$(PY) -m trade_sourcing_ai.evaluation --out reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

report:
	$(PY) scripts/run_demo.py --report-only

api:
	$(PY) -m uvicorn app:app --port 8000

lint:
	ruff check src/ tests/ scripts/
