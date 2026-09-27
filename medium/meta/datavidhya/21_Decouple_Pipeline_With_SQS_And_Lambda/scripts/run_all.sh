#!/usr/bin/env bash
# run_all.sh -- run the six mutating stages in sequence.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lab.sh"

for stage in 01_create_main_queue 02_create_dlq 03_attach_redrive \
             04_create_lambda 05_send_messages 06_send_poison; do
    echo
    echo "============================================================"
    echo "Running stage: $stage"
    echo "============================================================"
    bash "$SCRIPT_DIR/${stage}.sh"
done

echo
echo "[run_all] all six mutating stages complete."
echo "[run_all] inspect the DLQ + CloudWatch Logs before running 07_teardown.sh."