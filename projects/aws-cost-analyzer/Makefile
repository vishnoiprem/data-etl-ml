.PHONY: help up test demo eval fetch report lint

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "AWS Cost Analyzer commands:"
	@echo "  make up     - Install dependencies into the shared venv"
	@echo "  make test   - Run the pytest suite (offline: no creds, no network)"
	@echo "  make demo   - Run the offline end-to-end analysis on the fixtures"
	@echo "  make eval   - Run the eval harness (planted anomalies + gates)"
	@echo "  make fetch  - Pull live data from AWS (needs credentials)"
	@echo "  make report - Write the findings report to reports/"
	@echo "  make lint   - ruff check src/ tests/ scripts/ app.py"

up:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -v

smoke: demo

demo:
	$(PY) scripts/run_demo.py

eval:
	$(PY) -m aws_cost_analyzer.evaluation --out reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

fetch:
	$(PY) scripts/fetch_aws.py

report:
	$(PY) scripts/run_demo.py --report-only

lint:
	ruff check src/ tests/ scripts/ app.py
