.PHONY: help up test smoke demo eval report lint

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "CopyForge AI commands:"
	@echo "  make up     - Install dependencies into the shared venv"
	@echo "  make test   - Run the pytest suite (offline, no API key, no Ollama)"
	@echo "  make demo   - Run the offline end-to-end copy-insertion demo"
	@echo "  make eval   - Run the eval harness (rubric improvement over drafts)"
	@echo "  make report - Write the scoring report to reports/"
	@echo "  make lint   - ruff check src/ tests/ scripts/"

up:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -v

smoke: demo

demo:
	$(PY) scripts/run_demo.py

eval:
	$(PY) -m copyforge_ai.evaluation --out reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

report:
	$(PY) scripts/run_demo.py --report-only

lint:
	ruff check src/ tests/ scripts/
