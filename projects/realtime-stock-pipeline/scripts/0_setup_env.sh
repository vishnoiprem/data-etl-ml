#!/usr/bin/env bash
# 0_setup_env.sh — prepare local environment for the realtime stock pipeline.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Project root: $ROOT"

# 1. .env from .env.example
if [[ -f .env.example && ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
elif [[ -f .env ]]; then
  echo ".env already present (skipping copy)"
else
  echo "WARNING: no .env.example found; please create .env manually"
fi

# 2. producer package init
mkdir -p producer
[[ -f producer/__init__.py ]] || : > producer/__init__.py
echo "producer/__init__.py ensured"

# 3. Python check
PY_BIN=""
for cand in python3.11 python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    PY_BIN="$cand"
    break
  fi
done

if [[ -n "$PY_BIN" ]]; then
  ver=$("$PY_BIN" -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  echo "Found $PY_BIN ($ver)"
  major=$("$PY_BIN" -c 'import sys;print(sys.version_info[0])')
  minor=$("$PY_BIN" -c 'import sys;print(sys.version_info[1])')
  if (( major < 3 )) || (( major == 3 && minor < 11 )); then
    echo "WARNING: Python 3.11+ recommended. Please install (brew install python@3.11)."
  fi
else
  echo "WARNING: python3 not found on PATH. Install Python 3.11+ to run the producer locally."
fi

# 4. docker check (best-effort)
if command -v docker >/dev/null 2>&1; then
  echo "docker: $(docker --version)"
else
  echo "WARNING: docker CLI not found. Install Docker Desktop to run the stack."
fi

echo "Setup complete."
