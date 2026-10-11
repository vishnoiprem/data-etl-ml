#!/usr/bin/env bash
# Bootstrap a fresh machine:
#   1. Create .venv
#   2. Install deps
#   3. Copy .env.example to .env if missing
#   4. Start TimescaleDB
#   5. Initialize schema
#
# Author: Prem Vishnoi <pvishnoi@avilx.com>
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

echo "==> 1. Creating virtualenv"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "==> 2. Installing deps"
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo "==> 3. .env"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    created .env from .env.example (edit as needed)"
fi

echo "==> 4. Starting TimescaleDB"
docker compose up -d timescaledb

echo "==> 5. Waiting for TimescaleDB to be healthy"
for i in {1..30}; do
    if docker exec crypto-timescaledb pg_isready -U postgres >/dev/null 2>&1; then
        echo "    TimescaleDB is ready"
        break
    fi
    echo "    ($i/30) waiting…"
    sleep 2
done

echo "==> 6. Initializing schema"
python -c "from src.store.db import init_schema; init_schema()"

echo "==> Bootstrap complete. Try: make backfill && make test && make pipeline"
