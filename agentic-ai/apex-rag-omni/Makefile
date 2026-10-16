.PHONY: help up down index eval test lint api

help:
	@echo "APEX-RAG Omni commands:"
	@echo "  make up       - Bring up qdrant (10 shards), es, kafka, flink, postgres, redis"
	@echo "  make index    - Load 100M synthetic docs into all shards"
	@echo "  make eval     - Run the eval harness (Recall@8, nDCG, LLM-as-judge)"
	@echo "  make test     - Run pytest suite (27 legacy + 14 prod-hardening)"
	@echo "  make api      - Run the FastAPI backend on :8000"
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
	python -m eval.harness --out eval/reports/eval_$$(date -u +%Y-%m-%dT%H-%M-%SZ).json

test:
	pytest tests/ -v --cov=backend --cov=agent --cov=tools --cov=eval

api:
	APEX_API_KEYS=$${APEX_API_KEYS:-devkey-change-me} \
	uvicorn backend.app.main:app --reload --port 8000

lint:
	ruff check backend/ tests/ && mypy backend/