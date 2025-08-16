# dashboard.py
import streamlit as st
import redis
import json
import time
import pandas as pd

# Configure Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Dashboard UI
st.title("📊 Real-Time Order Analytics")
st.subheader("Live updates from PostgreSQL CDC → Kafka → Flink → Redis")

# Auto-refresh every 2 seconds
refresh_rate = st.slider("Refresh rate (seconds)", 1, 10, 2)

# Dashboard columns
col1, col2 = st.columns(2)

while True:
    # Get all user analytics from Redis
    user_data = []
    for key in r.scan_iter("user_analytics:*"):
        user = key.split(":")[1]
        data = json.loads(r.get(key))
        user_data.append({
            "User": user,
            "Total Orders": data["total_orders"],
            "Total Revenue": f"${data['total_revenue']:,.2f}"
        })

    # Display data
    with col1:
        st.metric("Active Users", len(user_data))
        st.write("### User Breakdown")
        st.table(pd.DataFrame(user_data))

    with col2:
        st.write("### Revenue Distribution")
        if user_data:
            chart_data = pd.DataFrame({
                "User": [d["User"] for d in user_data],
                "Revenue": [float(d["Total Revenue"].replace("$", "").replace(",", "")) for d in user_data]
            })
            st.bar_chart(chart_data.set_index("User"))

    time.sleep(refresh_rate)
    st.experimental_rerun()