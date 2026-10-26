#!/bin/bash
# .devcontainer/post-create.sh — runs once after the container is
# created. Sets up:
#   1. venv + install leads-pipeline runtime + test deps
#   2. Start the avilx-postgres container via the repo's
#      docker-compose.yml (already in the repo)
#   3. Apply the schema to avilx_test so leads-ci's tests pass
#      locally
#
# Idempotent — safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

DRAFTS="leads-pipeline/draft-cron"

# 1. venv + install
if [[ ! -d "$DRAFTS/.venv" ]]; then
  echo "→ creating venv at $DRAFTS/.venv"
  python3 -m venv "$DRAFTS/.venv"
fi
echo "→ installing runtime + test deps"
"$DRAFTS/.venv/bin/pip" install --quiet --upgrade pip
"$DRAFTS/.venv/bin/pip" install --quiet -r "$DRAFTS/requirements.txt"
"$DRAFTS/.venv/bin/pip" install --quiet flake8

# 2. start postgres via the repo's docker-compose
if ! docker ps --format '{{.Names}}' | grep -q '^avilx-postgres$'; then
  echo "→ starting avilx-postgres via docker-compose"
  ( cd "$DRAFTS" && docker compose up -d postgres )
  # wait for it to be ready
  echo -n "waiting for postgres"
  for i in {1..30}; do
    if docker exec avilx-postgres pg_isready -U avilx >/dev/null 2>&1; then
      echo " — ready"
      break
    fi
    echo -n "."
    sleep 1
  done
fi

# 3. create avilx_test DB and apply schema
echo "→ ensuring avilx_test DB exists"
docker exec avilx-postgres psql -U avilx -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='avilx_test'" \
  | grep -q 1 || docker exec avilx-postgres psql -U avilx -d postgres \
        -c "CREATE DATABASE avilx_test"

echo "→ applying schema to avilx_test"
docker exec -i avilx-postgres psql -U avilx -d avilx_test \
  < "$DRAFTS/db/schema.sql" >/dev/null

cat <<'EOF'

✅ devcontainer ready.

Quick start:
  cd leads-pipeline/draft-cron
  make ci            # install + test + lint + docker-build + smoke

  # or, against the running avilx-postgres:
  AVILX_DB_HOST=localhost AVILX_DB_PORT=5433 \
  AVILX_DB_NAME=avilx_test AVILX_DB_USER=avilx AVILX_DB_PASSWORD=avilx \
  make test
EOF
