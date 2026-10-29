#!/bin/bash

# Start all containers
# 1. Stop and remove all containers, networks, and volumes (if needed)
docker compose down

# 2. (Optional) Remove any old volumes if you want a fresh DB
#    ⚠️ Warning: This deletes your PostgreSQL data!
# docker compose down --volumes

# 3. Rebuild and start all services in detached mode
docker compose up -d

# 4. Watch logs to confirm everything starts correctly
docker compose logs -f

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Verify Kafka is running and list topics
echo "📋 Kafka topics:"
docker exec -it flink-cdc-dashboard-kafka-1 \
  kafka-topics.sh --bootstrap-server kafka:9092 --list

# Show success and next steps
echo "✅ Infrastructure is running!"
echo ""
echo "👉 Next steps:"
echo "   • Check Debezium Connect: http://localhost:8083"
echo "   • View logs: docker compose logs -f"
echo "   • Run CDC setup: sh 2_setup_cdc.sh"