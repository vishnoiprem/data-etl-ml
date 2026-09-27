#!/usr/bin/env bash
# run_all.sh -- execute the six lab stages against a real AWS account.
# Prerequisite: DATA_BUCKET and LOG_BUCKET exported (use 00_set_buckets.sh).
#
# Stage 6 is teardown -- skipped here so the bucket survives for inspection.
# Re-run 06_teardown.sh manually when done.
set -euo pipefail
: "${DATA_BUCKET:?Run 00_set_buckets.sh first}"
: "${LOG_BUCKET:?Run 00_set_buckets.sh first}"
HERE="$(cd "$(dirname "$0")" && pwd)"

"$HERE/00_set_buckets.sh"
"$HERE/01_inspect_buckets.sh"
"$HERE/02_lifecycle_rule.sh"
"$HERE/03_storage_transition.sh"
"$HERE/04_access_logging.sh"
"$HERE/05_read_log.sh"

echo
echo "[ok] stages 0-5 complete; run 06_teardown.sh when done with the lab."
