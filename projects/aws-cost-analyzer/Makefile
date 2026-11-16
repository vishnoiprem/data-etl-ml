.PHONY: help up test demo eval fetch report lint docker docker-run

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
	@echo "  make docker - Build the runtime container image"
	@echo "  make docker-run - Run the image on http://localhost:8000"

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

# The image the CD workflow publishes. It ships no AWS credentials and
# makes no AWS calls — it serves the analysis of whatever snapshot is
# present. `docker-run` mounts data/snapshots so a real snapshot can be
# served; without it, the app falls back to the synthetic corpus.
#
# The snapshot dir is created first: Docker would otherwise create the
# mount point as a root-owned directory, and `make fetch` could then not
# write into it.
docker:
	docker build -t aws-cost-analyzer:local .

docker-run: docker
	mkdir -p "$(CURDIR)/data/snapshots"
	docker run --rm -p 8000:8000 -v "$(CURDIR)/data/snapshots:/app/data/snapshots:ro" aws-cost-analyzer:local
