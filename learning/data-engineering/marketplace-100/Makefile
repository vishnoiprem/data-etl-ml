# Makefile — marketplace-100
#
# Local targets mirror the DAB deploy + run flow so a developer
# can iterate without round-tripping through the Databricks CLI.
#
# Targets:
#   make help         show all
#   make install      set up .venv with runtime + test deps
#   make test         run the full pytest suite
#   make lint         ruff check on src/ + tests/
#   make smoke        run 1 iteration end-to-end with all externals mocked
#   make bench        run 25-iter benchmark and emit measured numbers
#   make build        build the Python wheel for DAB upload
#   make validate     databricks bundle validate (needs DATABRICKS_HOST + TOKEN)
#   make deploy       databricks bundle deploy --target dev
#   make run          databricks bundle run m100_driver_job

HERE       := $(shell pwd)
PY         ?= $(HERE)/.venv/bin/python
VENV       := $(HERE)/.venv
DBX        ?= databricks
DAB_TARGET ?= dev
BENCH_ITERATIONS ?= 25

.PHONY: help install test lint smoke bench build clean validate deploy run

help:           ## show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:        ## create .venv and install deps
	@test -x $(PY) || python3 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -e ".[dev]"

test:           ## run the full pytest suite
	@echo "Running pytest"
	PYTHONPATH=$(HERE)/src $(PY) -m pytest tests/ -v

lint:           ## ruff check
	$(PY) -m ruff check src/ tests/

smoke:          ## run 1 iteration end-to-end with all externals mocked
	PYTHONPATH=$(HERE)/src $(PY) -m m100.smoke

bench:          ## run end-to-end benchmark (every component, real numbers)
	PYTHONPATH=$(HERE)/src $(PY) -m m100.benchmark --iterations $(BENCH_ITERATIONS) --json-out /tmp/m100_bench.json

build:          ## build the Python wheel for DAB upload
	$(PY) -m pip install --quiet --upgrade build
	$(PY) -m build --wheel --outdir dist/

validate:       ## databricks bundle validate
	$(DBX) bundle validate --target $(DAB_TARGET)

deploy:         ## databricks bundle deploy to dev
	$(DBX) bundle deploy --target $(DAB_TARGET)

run:            ## databricks bundle run m100_driver_job
	$(DBX) bundle run m100_driver_job --target $(DAB_TARGET)

clean:          ## remove build artifacts (NOT .venv)
	rm -rf $(HERE)/dist $(HERE)/build $(HERE)/*.egg-info
	find $(HERE) -name '__pycache__' -type d -exec rm -rf {} +
	find $(HERE) -name '*.pyc' -delete
