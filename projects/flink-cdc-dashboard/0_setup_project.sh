#!/bin/bash

# Create required directories
mkdir -p queries output dashboard

# Create init.sql
cat > init.sql <<EOF
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (user_id, amount) VALUES
('user1', 50.00),
('user2', 75.00);
EOF

# Create Flink SQL job
mkdir -p queries
cat > queries/orders_pipeline.sql <<EOF
CREATE TABLE orders_cdc (
  before ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  after ROW<id INT, user_id STRING, amount DECIMAL(10,2)>,
  op STRING,
  ts_ms BIGINT
) WITH (
  'connector' = 'kafka',
  'topic' = 'postgres.public.orders',
  'properties.bootstrap.servers' = 'kafka:29092',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'debezium-json'
);

CREATE TABLE redis_sink (
  user_id STRING,
  total_orders INT,
  total_revenue DECIMAL(10,2),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'redis',
  'host' = 'redis',
  'port' = '6379',
  'format' = 'json',
  'mode' = 'hash',
  'key' = 'user_analytics'
);

INSERT INTO redis_sink
SELECT
  after.user_id,
  COUNT(*) as total_orders,
  SUM(after.amount) as total_revenue
FROM orders_cdc
WHERE op = 'c' OR op = 'u'
GROUP BY after.user_id;
EOF

# Create dashboard files
cat > dashboard/data_generator.py <<EOF
import psycopg2
import random
import time
from faker import Faker

fake = Faker()

def generate_orders():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )

    print("🛒 Generating live orders...")
    while True:
        try:
            with conn.cursor() as cur:
                user_id = f"user_{random.randint(1, 10)}"
                amount = round(random.uniform(10, 500), 2)

                cur.execute(
                    "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                    (user_id, amount)
                )
                conn.commit()
                print(f"Inserted: {user_id}, ${amount:.2f}")
        except Exception as e:
            print(f"Error: {e}")
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="postgres"
            )

        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    generate_orders()
EOF

cat > dashboard/dashboard.py <<EOF
import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import time
import os

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

st.set_page_config(layout="wide")
st.title("📊 Real-Time Order Analytics Dashboard")
st.caption("Live data from PostgreSQL → Kafka → Flink → Redis")

refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 10, int(os.getenv("DASHBOARD_REFRESH", 5)))
threshold = st.sidebar.number_input("High spender threshold ($)", 1000)

def get_redis_data():
    users = []
    for key in r.scan_iter("user_analytics:*"):
        data = json.loads(r.get(key))
        users.append({
            "User": key.split(":")[1],
            "Total Orders": data["total_orders"],
            "Total Revenue": float(data["total_revenue"])
        })
    return pd.DataFrame(users) if users else pd.DataFrame()

placeholder = st.empty()
while True:
    with placeholder.container():
        df = get_redis_data()
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Users", len(df))
            col2.metric("Total Revenue", f"${df['Total Revenue'].sum():,.2f}")
            col3.metric("Avg Order Value", f"${df['Total Revenue'].sum()/df['Total Orders'].sum():,.2f}")

            fig1 = px.bar(df, x="User", y="Total Revenue", title="Revenue by User")
            st.plotly_chart(fig1, use_container_width=True)

            high_spenders = df[df["Total Revenue"] > threshold]
            if not high_spenders.empty:
                st.warning("🚨 High Spenders Alert!")
                st.dataframe(high_spenders)

    time.sleep(refresh_rate)
EOF

cat > requirements.txt <<EOF
streamlit
pandas
plotly
redis
EOF

echo "✅ Project setup complete!"