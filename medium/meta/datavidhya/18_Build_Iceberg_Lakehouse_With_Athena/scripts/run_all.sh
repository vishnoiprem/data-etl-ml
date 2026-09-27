#!/usr/bin/env bash
# run_all.sh -- run the seven mutating stages in sequence.
#
# Stage 0 (set_lakehouse.sh) is run separately because it requires
# pasting the lab-provided names. Stage 8 (teardown) is also separate so
# you can inspect the bucket state before destroying it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/00_set_lakehouse.sh"

for stage in 01_register_csv 02_ctas_iceberg 03_update 04_delete \
             05_time_travel 06_insert 07_metadata; do
    echo
    echo "============================================================"
    echo "Running stage: $stage"
    echo "============================================================"
    bash "$SCRIPT_DIR/${stage}.sh"
    sleep 3   # let Athena finish the prior query
done

echo
echo "[run_all] all seven mutating stages complete."
echo "[run_all] inspect the bucket before running 08_teardown.sh."
