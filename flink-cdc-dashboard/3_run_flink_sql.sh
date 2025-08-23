#!/bin/bash

# Execute Flink SQL job
echo "⚡ Running Flink SQL pipeline..."
docker exec -d flink-sql-client-1 \
  /opt/flink/bin/sql-client.sh -f /opt/queries/orders_pipeline.sql

echo "✅ Flink SQL job started in background!"
echo "ℹ️ Check logs with: docker logs flink-sql-client-1"