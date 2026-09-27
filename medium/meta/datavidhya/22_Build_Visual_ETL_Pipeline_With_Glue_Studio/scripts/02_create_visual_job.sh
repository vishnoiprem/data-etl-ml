#!/usr/bin/env bash
# 02_create_visual_job.sh -- lab stage 2: create the visual Glue Studio job.
#
# In Glue Studio the visual graph lives in the lab console; we don't
# upload it. The job is identified by its name; running it triggers the
# visual graph defined in the UI.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

JOB_NAME="customer-visual-etl-q22"

echo "[lab-stage-2] creating visual Glue Studio job: $JOB_NAME"
aws glue create-job \
    --name "$JOB_NAME" \
    --role "$ROLE_ARN" \
    --command "Name=gluestudio,JobMode=VISUAL,PythonVersion=3" \
    --default-arguments "{\"--input_path\":\"s3://$BUCKET/raw/\",\"--output_path\":\"s3://$BUCKET/curated/customers/\",\"--job-language\":\"python\"}" \
    --glue-version 4.0 \
    --worker-type Standard \
    --number-of-workers 2 \
    --region "$AWS_REGION"

echo
echo "[lab-stage-2] job created.  Build the visual graph in Glue Studio,"
echo "              then run 03_run_visual_job.sh to execute it."
