#!/usr/bin/env bash
# run_all.sh -- run the six mutating stages in sequence.
#
# Stage 0 (set_lab.sh) is run separately because it requires pasting the
# lab-provided names from the AWS console. Stage 7 (teardown) is also
# separate so you can inspect the catalog before destroying it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

for stage in 01_inspect_bucket 02_create_crawler 03_run_crawler \
             04_review_schemas 05_fix_schema 06_query_join; do
    echo
    echo "============================================================"
    echo "Running stage: $stage"
    echo "============================================================"
    bash "$SCRIPT_DIR/${stage}.sh"
done

echo
echo "[run_all] all six mutating stages complete."
echo "[run_all] inspect the catalog before running 07_teardown.sh."
