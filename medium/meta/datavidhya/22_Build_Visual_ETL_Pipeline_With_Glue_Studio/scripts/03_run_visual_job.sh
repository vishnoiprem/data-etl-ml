#!/usr/bin/env bash
# 03_run_visual_job.sh -- lab stage 3: start the visual job, poll until SUCCEEDED.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

JOB_NAME="customer-visual-etl-q22"

echo "[lab-stage-3] starting job run: $JOB_NAME"
RUN_ID=$(aws glue start-job-run --job-name "$JOB_NAME" \
          --region "$AWS_REGION" \
          --query 'JobRunId' --output text)
echo "[lab-stage-3] JobRunId=$RUN_ID"

echo "[lab-stage-3] polling JobRunState every 15s..."
while true; do
    STATE=$(aws glue get-job-run --job-name "$JOB_NAME" \
              --run-id "$RUN_ID" --region "$AWS_REGION" \
              --query 'JobRun.JobRunState' --output text)
    echo "  state=$STATE"
    case "$STATE" in
        SUCCEEDED)  echo "[lab-stage-3] job succeeded."; break ;;
        FAILED|STOPPED|TIMEOUT|ERROR)
            echo "[lab-stage-3] job ended in $STATE."
            aws glue get-job-run --job-name "$JOB_NAME" \
                --run-id "$RUN_ID" --region "$AWS_REGION" \
                --query 'JobRun.ErrorMessage' --output text
            exit 1 ;;
    esac
    sleep 15
done