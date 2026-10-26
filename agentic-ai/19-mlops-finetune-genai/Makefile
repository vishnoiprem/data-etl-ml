.PHONY: up test smoke train serve monitor clean

# House style (matches 17-computer-use-agent, 16-autonomous-loop):
#   up:    install dependencies
#   test:  pytest, gated on HAVE_PEFT so CI passes without a GPU
#   smoke: 1-step synthetic SFT + vLLM wire-test
#   train: full QLoRA on FineTome-100k subset, MLflow + Grafana included
#   serve: docker compose up vllm + mlflow + prometheus + grafana
#   monitor: tail drift + cost
#   clean: tear down containers + remove local artifacts

UP_ARGS ?=
TEST_ARGS ?=

up:
	pip install -r requirements.txt

test:
	pytest -q $(TEST_ARGS)

smoke:
	@echo ">> synthetic-mode smoke: 16 rows, 1 step, no GPU required"
	@HF_DATASET_OFFLINE=1 PYTHONPATH=. python tests/test_smoke_synthetic.py

train:
	@echo ">> full QLoRA SFT on FineTome-100k subset"
	@docker compose -f infra/docker-compose.yml up -d mlflow
	@bash scripts/run_pipeline.sh

serve:
	@echo ">> spinning up vllm + mlflow + prometheus + grafana"
	@docker compose -f infra/docker-compose.yml up -d
	@sleep 4
	@echo "vLLM:   http://localhost:8000"
	@echo "MLflow: http://localhost:5000"
	@echo "Grafana: http://localhost:3000  (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

monitor:
	@echo ">> monitoring dashboard"
	@curl -s http://localhost:9090/api/v1/query?query=up | python -m json.tool | head -40
	@echo ""
	@echo ">> drift score:"
	@curl -s http://localhost:9090/api/v1/query?query=model_drift_score | python -m json.tool | head -40

clean:
	@docker compose -f infra/docker-compose.yml down -v
	@rm -rf .cache data/ mlruns/ sft-output/ artifacts/ vllm-cache/ eval-output/ \
		__pycache__ */__pycache__ */*/__pycache__ *.log
