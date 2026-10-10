#!/usr/bin/env bash
# Bootstrap the dbt + Snowflake course on a fresh machine.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo
echo "Course bootstrapped. Run:"
echo "  python scripts/run_all_tests.py"
