#!/usr/bin/env bash
# scripts/bootstrap.sh — one-shot bring-up of the full MLOps stack.
#
# Steps:
#   1. Make sure .env exists; copy from .env.example if not.
#   2. `docker compose up -d` — mlflow + vllm + prometheus + grafana.
#   3. Wait for mlflow healthcheck to be green.
#   4. Create-or-fetch the MLflow experiment `mlops-finetune-genai`.
#   5. Capture a drift baseline (synthetic) so Grafana has a panel value.
#
# Idempotent: re-running leaves the stack running.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. .env bootstrap
if [[ ! -f .env ]]; then
  echo ">> .env not found, copying from .env.example"
  cp .env.example .env
fi

# 2. compose
echo ">> docker compose up -d"
docker compose -f infra/docker-compose.yml up -d

# 3. mlflow wait
echo ">> waiting for mlflow healthcheck"
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:5000/api/2.0/mlflow/experiments/list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

# 4. experiment
EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-mlops-finetune-genai}"
TRACKING_URI="${MLFLOW_TRACKING_URI:-http://localhost:5000}"
echo ">> ensuring MLflow experiment '$EXPERIMENT_NAME' exists"
python -c "
import os, mlflow
mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URI', '$TRACKING_URI'))
mlflow.set_experiment(os.environ.get('MLFLOW_EXPERIMENT_NAME', '$EXPERIMENT_NAME'))
print('OK')
"

# 5. drift baseline
echo ">> capturing drift baseline (synthetic)"
mkdir -p artifacts
python -c "
import os
os.environ.setdefault('MLFLOW_TRACKING_URI', '$TRACKING_URI')
import numpy as np
import pandas as pd
rng = np.random.default_rng(0)
df = pd.DataFrame(rng.normal(size=(512, 16)), columns=[f'f{i}' for i in range(16)])
df.to_parquet('artifacts/drift_baseline.parquet')
print('wrote artifacts/drift_baseline.parquet')
"

echo ""
echo "=== stack is up ==="
echo "  vLLM:     http://localhost:8000"
echo "  MLflow:   http://localhost:5000"
echo "  Prom:     http://localhost:9091"
echo "  Grafana:  http://localhost:3000  (admin/admin)"
echo ""
echo "next:"
echo "  make train   # run the full QLoRA SFT"
echo "  make monitor # tail the drift detector"
