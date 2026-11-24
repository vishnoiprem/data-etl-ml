.PHONY: help up test smoke demo eval report lint api clean

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

help:
	@echo "TMS E-commerce Logistics commands:"
	@echo "  make up     - Install dependencies into the shared venv"
	@echo "  make test   - Run the pytest suite (offline, no API key)"
	@echo "  make demo   - Run the offline end-to-end delivery demo"
	@echo "  make eval   - Run the eval harness (detection gates + decision accuracy)"
	@echo "  make report - Write the KPI report to reports/"
	@echo "  make api    - Run the FastAPI app on :8000"
	@echo "  make lint   - ruff check src/ tests/ scripts/ app.py"
	@echo "  make clean  - Remove generated reports"

up:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest tests/ -v

smoke: demo

demo:
	$(PY) scripts/run_demo.py

eval:
	$(PY) -m tms.evaluation --out reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

report:
	$(PY) scripts/run_demo.py --report-only

api:
	$(PY) -m uvicorn app:app --port 8000

lint:
	ruff check src/ tests/ scripts/ app.py

clean:
	rm -rf reports/*.json reports/*.md
