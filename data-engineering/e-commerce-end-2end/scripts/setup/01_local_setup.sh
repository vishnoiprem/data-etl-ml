#!/bin/bash
# ============================================================
# Local Setup Script - E-Commerce End-to-End Pipeline
# ============================================================
set -e

echo "============================================================"
echo " E-Commerce Data Pipeline - Local Setup"
echo "============================================================"

# ── Python environment ────────────────────────────────────────
echo ""
echo "[1/5] Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "  ✅ Python dependencies installed"

# ── Docker services ───────────────────────────────────────────
echo ""
echo "[2/5] Starting Docker services (MySQL, Kafka, ClickHouse)..."
docker compose -f docker/docker-compose.yml up -d mysql zookeeper kafka clickhouse
echo "  Waiting for services to be healthy..."
sleep 30
echo "  ✅ Core services started"

# ── MySQL seed ────────────────────────────────────────────────
echo ""
echo "[3/5] Seeding MySQL with dummy data..."
source .venv/bin/activate
python source_mysql/dummy_data/02_seed_data.py
echo "  ✅ MySQL seeded"

# ── Kafka topics ─────────────────────────────────────────────
echo ""
echo "[4/5] Creating Kafka topics..."
docker exec ecomm-kafka kafka-topics --create \
  --bootstrap-server kafka:9092 \
  --topic ecomm.cdc.orders \
  --partitions 6 --replication-factor 1 2>/dev/null || true

for topic in order_items inventory user_events payments shipments product_skus reviews; do
  docker exec ecomm-kafka kafka-topics --create \
    --bootstrap-server kafka:9092 \
    --topic "ecomm.cdc.$topic" \
    --partitions 6 --replication-factor 1 2>/dev/null || true
done
echo "  ✅ Kafka topics created"

# ── ClickHouse schema ─────────────────────────────────────────
echo ""
echo "[5/5] Applying ClickHouse schema..."
docker exec -i ecomm-clickhouse clickhouse-client \
  --password clickhouse123 \
  < realtime_pipeline/clickhouse/schemas/01_clickhouse_schema.sql
echo "  ✅ ClickHouse schema applied"

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Setup Complete! Services running at:"
echo ""
echo "  MySQL           → localhost:3306"
echo "  Kafka           → localhost:29092"
echo "  Kafka UI        → http://localhost:8080"
echo "  ClickHouse HTTP → http://localhost:8123"
echo "  Flink UI        → http://localhost:8081"
echo "  BI API Docs     → http://localhost:8000/api/docs"
echo "  BI Dashboard    → http://localhost:3000"
echo "  Grafana         → http://localhost:3001  (admin/admin123)"
echo "============================================================"
