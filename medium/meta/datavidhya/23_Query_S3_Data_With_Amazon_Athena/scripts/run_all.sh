#!/usr/bin/env bash
# run_all.sh -- run the five mutating stages in sequence.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

for stage in 01_inspect_s3 02_create_database 03_create_table \
             04_run_queries 05_challenge_query; do
    echo
    echo "============================================================"
    echo "Running stage: $stage"
    echo "============================================================"
    bash "$SCRIPT_DIR/${stage}.sh"
done

echo
echo "[run_all] all five mutating stages complete."
echo "[run_all] inspect the Athena results in the workgroup before running 06_teardown.sh."