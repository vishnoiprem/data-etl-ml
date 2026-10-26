#!/usr/bin/env bash
# Smoke-test every system-design module.
#
# Usage:
#   bash scripts/run_all_smoke_tests.sh
#
# Exits 0 if every test module runs (non-zero tests may pass or fail —
# we only check that they RUN). Set VERBOSE=1 for full unittest -v output.

set -uo pipefail

cd "$(dirname "$0")/.."

VERBOSE="${VERBOSE:-0}"
ARGS=()
if [[ "$VERBOSE" == "1" ]]; then
  ARGS=(-v)
fi

mkdir -p var/logs
LOG="var/logs/smoke-$(date +%Y%m%d-%H%M%S).log"

FAILS=()
RUNS=0

for module_dir in $(ls -d ??_* 2>/dev/null | sort); do
  if [[ -d "$module_dir/tests" ]]; then
    echo "==> $module_dir"
    if python3 -m unittest discover -s "$module_dir/tests" -p "test_*.py" "${ARGS[@]}" \
         >> "$LOG" 2>&1; then
      echo "    ok"
    else
      echo "    FAILED (see $LOG)"
      FAILS+=("$module_dir")
    fi
    RUNS=$((RUNS+1))
  fi
done

echo
echo "Ran $RUNS test suites. Failures: ${#FAILS[@]}"
if (( ${#FAILS[@]} > 0 )); then
  printf '  - %s\n' "${FAILS[@]}"
fi
echo "Full log: $LOG"
