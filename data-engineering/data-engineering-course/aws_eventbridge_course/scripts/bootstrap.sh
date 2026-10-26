#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if command -v aws >/dev/null 2>&1; then
  echo "aws CLI found: $(aws --version)"
else
  echo "aws CLI not found (optional — only needed for the boto3 scripts against a real account)."
fi
python scripts/run_all_tests.py
