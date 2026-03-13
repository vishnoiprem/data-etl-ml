#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Makro Superset Bootstrap Script
# Runs ONCE on first start via superset-init service.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "================================================"
echo "  Makro Data Service Platform — Superset Init  "
echo "================================================"

# 1. Upgrade Superset metadata DB
echo "[1/5] Upgrading Superset database..."
superset db upgrade

# 2. Create admin user
echo "[2/5] Creating admin user: ${ADMIN_USERNAME}..."
superset fab create-admin \
  --username "${ADMIN_USERNAME}" \
  --firstname "${ADMIN_FIRSTNAME}" \
  --lastname  "${ADMIN_LASTNAME}" \
  --email     "${ADMIN_EMAIL}" \
  --password  "${ADMIN_PASSWORD}" || echo "Admin user already exists, skipping."

# 3. Initialize default roles and permissions
echo "[3/5] Initialising roles and permissions..."
superset init

# 4. Register Databricks connection + create datasets/dashboards
echo "[4/5] Bootstrapping Databricks connection and dashboards..."
python /app/docker/docker-init.d/bootstrap_dashboards.py

# 5. Done
echo "[5/5] Init complete ✓"
echo ""
echo "  Superset is ready at http://localhost:8088"
echo "  Login: ${ADMIN_USERNAME} / ${ADMIN_PASSWORD}"
echo ""
