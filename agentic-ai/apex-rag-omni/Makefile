.PHONY: help up down index eval test lint

help:
	@echo "APEX-RAG Omni commands:"
	@echo "  make up       - Bring up qdrant (10 shards), es, kafka, flink, postgres, redis"
	@echo "  make index    - Load 100M synthetic docs into all shards"
	@echo "  make eval     - Run the eval harness (Recall@8, nDCG, LLM-as-judge)"
	@echo "  make test     - Run pytest suite"
	@echo "  make down     - Tear down infra"

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down -v

index:
	python -m agent.indexer --docs 100000000 --shards 10

eval:
	python -m eval.harness --out reports/eval_$(shell date -u +%Y-%m-%dT%H-%M-%SZ).json

test:
	pytest tests/ -v --cov=agent --cov=tools --cov=eval

lint:
	ruff check . && mypy agent tools eval