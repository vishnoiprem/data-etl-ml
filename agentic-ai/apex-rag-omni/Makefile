.PHONY: help up down index eval test lint api web

# Use the shared parent venv (data-etl-ml/.env) when present, else PATH.
VENV := $(abspath ../../.env/bin)
PY   := $(if $(wildcard $(VENV)/python),$(VENV)/python,python3)

help:
	@echo "APEX-RAG Omni commands:"
	@echo "  make up       - Bring up qdrant (10 shards), es, kafka, flink, postgres, redis"
	@echo "  make index    - Load 100M synthetic docs into all shards"
	@echo "  make eval     - Run the eval harness (Recall@8, nDCG, LLM-as-judge)"
	@echo "  make test     - Run pytest suite (legacy + API + grounding + safety)"
	@echo "  make api      - Run the FastAPI backend on :8000"
	@echo "  make web      - Run the Next.js chat UI on :3000 (start make api first)"
	@echo "  make down     - Tear down infra"

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down -v

index:
	python -m agent.indexer --docs 100000000 --shards 10

eval:
	# Runs the harness against the dummy retriever (same as TestEndToEnd).
	# Writes to eval/reports/eval_<ts>.json. /eval then reads the latest.
	APEX_API_KEYS=$${APEX_API_KEYS:-devkey-change-me} \
	$(PY) -m eval.harness --out eval/reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

test:
	$(PY) -m pytest tests/ -v 

api:
	APEX_API_KEYS=$${APEX_API_KEYS:-devkey-change-me} \
	$(PY) -m uvicorn backend.app.main:app --reload --port 8000

web:
	cd frontend && npm install --no-audit --no-fund && npm run dev

lint:
	ruff check backend/ tests/ && mypy backend/