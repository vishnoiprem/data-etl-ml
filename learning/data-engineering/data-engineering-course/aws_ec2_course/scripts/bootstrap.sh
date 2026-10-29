#!/usr/bin/env bash
# Bootstrap the EC2 course environment.
#   1. Create .venv (if missing)
#   2. Install requirements
#   3. Verify aws CLI is on PATH (optional, only needed for real AWS)
#   4. Run the test suite
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if command -v aws >/dev/null 2>&1; then
  echo "aws CLI found: $(aws --version)"
else
  echo "aws CLI not found (optional — only needed for the boto3 scripts against a real account)."
fi

python scripts/run_all_tests.py
