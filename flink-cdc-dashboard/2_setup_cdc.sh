#!/bin/bash

MAX_WAIT=120
WAIT_TIME=0

echo "⏳ Waiting for Debezium Connect to start (timeout: ${MAX_WAIT}s)..."
while ! curl -s http://localhost:8083/ > /dev/null; do
  sleep 5
  WAIT_TIME=$((WAIT_TIME + 5))
  if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo "❌ Timeout waiting for Connect! Last 20 logs:"
    docker compose logs --tail=20 connect
    echo "ℹ️ Run 'docker compose ps' and 'docker compose logs connect' for more details."
    exit 1
  fi
done

echo "🚀 Configuring PostgreSQL CDC connector..."
response=$(curl -s -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "orders-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "postgres",
      "database.dbname": "postgres",
      "database.server.name": "postgres",
      "plugin.name": "pgoutput",
      "table.include.list": "public.orders",
      "key.converter.schemas.enable": "false",
      "value.converter.schemas.enable": "false"
    }
  }')

if [[ "$response" == *"error_code"* ]]; then
  echo "❌ Failed to configure connector:"
  echo "$response"
else
  echo "✅ Successfully configured CDC connector!"
  echo "ℹ️ Verify status: curl http://localhost:8083/connectors/orders-connector/status"
fi