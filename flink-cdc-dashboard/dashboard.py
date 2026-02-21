import streamlit as st
import redis
import json
import pandas as pd
import plotly.express as px
import time
import os

# Configure Redis from environment variables
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Dashboard setup
st.set_page_config(layout="wide")
st.title("📊 Real-Time Order Analytics Dashboard")
st.caption("Live data from PostgreSQL → Kafka → Flink → Redis")

# Sidebar controls
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
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Users", len(df))
            col2.metric("Total Revenue", f"${df['Total Revenue'].sum():,.2f}")
            col3.metric("Avg Order Value", f"${df['Total Revenue'].sum() / df['Total Orders'].sum():,.2f}")

            # Charts
            fig1 = px.bar(df, x="User", y="Total Revenue", title="Revenue by User")
            st.plotly_chart(fig1, use_container_width=True)

            # High spenders
            high_spenders = df[df["Total Revenue"] > threshold]
            if not high_spenders.empty:
                st.warning("🚨 High Spenders Alert!")
                st.dataframe(high_spenders)

    time.sleep(refresh_rate)