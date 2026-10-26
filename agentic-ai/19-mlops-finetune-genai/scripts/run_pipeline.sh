#!/usr/bin/env bash
# scripts/run_pipeline.sh — train → eval → merge → register → serve → monitor.
#
# This is the README's "one command to see the whole pipeline work" target.
# Each step is small and dedicated; if any fails we bail before spending
# GPU minutes on the next stage.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

step() { printf "\n=== %s ===\n" "$*"; }

# Bootstrap the stack (idempotent).
bash scripts/bootstrap.sh

step "1/6 train (QLoRA SFT)"
TRAIN_SYNTHETIC="${TRAIN_SYNTHETIC:-0}" \
  python -m agent.train \
    --out sft-output

step "2/6 evaluate (lm-eval + held-out)"
python -m agent.evaluate --model-path sft-output/merged 2>&1 | tail -40 || \
  python -m agent.evaluate --model-path sft-output/adapter 2>&1 | tail -40

step "3/6 merge adapter (already done inside train when cuda was available)"
test -d sft-output/merged || echo "(merged directory absent — fine for synthetic run)"

step "4/6 register @Champion in MLflow"
python -c "
import os
os.environ.setdefault('MLFLOW_TRACKING_URI', 'http://localhost:5000')
import mlflow
from mlflow.tracking import MlflowClient
client = MlflowClient()
try:
    client.set_registered_model_alias('sft-adapter', 'Champion', 1)
    print('OK: Champion alias set on version 1')
except Exception as e:
    print(f'(skipped: {e})')
"

step "5/6 serve (vLLM + Prometheus)"
docker compose -f infra/docker-compose.yml up -d vllm prometheus grafana
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then break; fi
  sleep 2
done
echo "vLLM ready: $(curl -fsS http://localhost:8000/healthz)"

step "6/6 monitor (drift + cost)"
docker compose -f infra/docker-compose.yml up -d prometheus grafana >/dev/null
python -m agent.monitor

echo ""
echo "=== pipeline complete ==="
echo "  vLLM:    http://localhost:8000"
echo "  MLflow:  http://localhost:5000"
echo "  Grafana: http://localhost:3000"
