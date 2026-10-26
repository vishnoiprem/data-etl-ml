# SCB AML Platform — common dev workflows
#
# Quick reference:
#   make help        Show this help
#   make install     Install runtime + dev deps
#   make test        Run the test suite
#   make lint        Run ruff + black --check
#   make format      Auto-format with black + ruff
#   make demo        Run the full pipeline + interactive demo
#   make api         Start the Lucid Search API
#   make airflow     Print the Airflow setup instructions

.PHONY: help install test test-cov lint format demo api airflow clean

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

help:
	@echo "SCB AML Platform — Makefile targets"
	@echo ""
	@echo "  make install   Install runtime + dev dependencies"
	@echo "  make test      Run the test suite (pytest)"
	@echo "  make test-cov  Run tests with coverage report"
	@echo "  make lint      Run ruff + black --check"
	@echo "  make format    Auto-format with black + ruff"
	@echo "  make demo      Run the full pipeline + interactive demo"
	@echo "  make api       Start the Lucid Search API (uvicorn)"
	@echo "  make airflow   Print Airflow setup instructions"
	@echo "  make clean     Remove generated data/, output/, __pycache__/"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -v

test-cov:
	$(PYTHON) -m pytest tests/ -v --cov=scb_aml_platform --cov-report=term-missing

lint:
	$(PYTHON) -m ruff check scb_aml_platform/ tests/
	$(PYTHON) -m black --check scb_aml_platform/ tests/

format:
	$(PYTHON) -m ruff check --fix scb_aml_platform/ tests/
	$(PYTHON) -m black scb_aml_platform/ tests/

demo:
	cd .. && $(PYTHON) scb_aml_platform/run_demo.py

api:
	cd .. && $(PYTHON) -m uvicorn scb_aml_platform.lucid_search.api.app:app \
		--host 0.0.0.0 --port 8000 --reload

airflow:
	@echo "Airflow lives in a separate venv (see requirements-airflow.txt):"
	@echo ""
	@echo "  python -m venv venv-airflow"
	@echo "  source venv-airflow/bin/activate"
	@echo "  pip install -r requirements-airflow.txt"
	@echo "  export AIRFLOW_HOME=~/airflow"
	@echo "  airflow db migrate"
	@echo "  cp orchestration/airflow_dag.py \$$AIRFLOW_HOME/dags/"
	@echo "  airflow api-server --port 8080 &"
	@echo "  airflow scheduler &"

clean:
	rm -rf data/ output/ logs/ .pytest_cache/ .ruff_cache/ .mypy_cache/ .coverage htmlcov/
	find scb_aml_platform/ tests/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find scb_aml_platform/ tests/ -type f -name "*.pyc" -delete
