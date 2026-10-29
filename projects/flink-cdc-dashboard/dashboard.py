"""Real-time order analytics dashboard with Streamlit."""

import json
import logging
import os
from typing import Optional

import pandas as pd
import plotly.express as px
import redis
import streamlit as st
from redis.exceptions import RedisError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@st.cache_resource
def get_redis_client() -> redis.Redis:
    """Create and cache Redis client with connection pooling."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
        max_connections=10,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
    )


def get_redis_data(
    client: redis.Redis,
    key_pattern: str = "user_analytics:*"
) -> pd.DataFrame:
    """Fetch user analytics from Redis.

    Args:
        client: Redis client instance
        key_pattern: Pattern to match Redis keys

    Returns:
        DataFrame with user analytics
    """
    users = []
    try:
        for key in client.scan_iter(match=key_pattern, count=100):
            data = client.get(key)
            if data:
                try:
                    parsed = json.loads(data)
                    users.append({
                        "User": key.split(":")[-1],
                        "Total Orders": parsed.get("total_orders", 0),
                        "Total Revenue": float(parsed.get("total_revenue", 0.0)),
                    })
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning("Failed to parse data for key %s: %s", key, e)
    except RedisError as e:
        logger.error("Redis error while fetching analytics: %s", e)
        st.error(f"Redis connection error: {e}")
    except Exception as e:
        logger.exception("Unexpected error fetching data: %s", e)
        st.error(f"Unexpected error: {e}")

    return pd.DataFrame(users) if users else pd.DataFrame()


def render_metrics(df: pd.DataFrame) -> None:
    """Render key metrics row."""
    if df.empty:
        st.info("No analytics data available yet")
        return

    total_orders = int(df["Total Orders"].sum())
    total_revenue = df["Total Revenue"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", len(df))
    col2.metric("Total Revenue", f"${total_revenue:,.2f}")
    col3.metric(
        "Avg Order Value",
        f"${total_revenue / total_orders:,.2f}" if total_orders > 0 else "$0.00"
    )


def render_charts(df: pd.DataFrame) -> None:
    """Render visualization charts."""
    if df.empty:
        return

    # Revenue by User - Bar Chart
    fig1 = px.bar(
        df.sort_values("Total Revenue", ascending=True),
        x="Total Revenue",
        y="User",
        orientation="h",
        title="Revenue by User",
        labels={"Total Revenue": "Revenue ($)", "User": "User ID"},
    )
    fig1.update_layout(height=max(300, len(df) * 35))
    st.plotly_chart(fig1, use_container_width=True)

    # Orders vs Revenue - Scatter
    fig2 = px.scatter(
        df,
        x="Total Orders",
        y="Total Revenue",
        hover_data=["User"],
        title="Orders vs Revenue",
        labels={"Total Orders": "Number of Orders", "Total Revenue": "Revenue ($)"},
    )
    st.plotly_chart(fig2, use_container_width=True)


def render_high_spenders(df: pd.DataFrame, threshold: float) -> None:
    """Render high spender alerts."""
    if df.empty:
        return

    high_spenders = df[df["Total Revenue"] > threshold]
    if not high_spenders.empty:
        st.warning(f"🚨 {len(high_spenders)} High Spender(s) Above ${threshold:,.2f}!")
        st.dataframe(
            high_spenders.sort_values("Total Revenue", ascending=False),
            use_container_width=True
        )


def main() -> None:
    """Main dashboard entry point."""
    st.set_page_config(
        page_title="Real-Time Order Analytics",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📊 Real-Time Order Analytics Dashboard")
    st.caption("Live data from PostgreSQL → Kafka → Flink → Redis")

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        refresh_rate = st.slider(
            "Refresh rate (seconds)",
            min_value=1,
            max_value=30,
            value=int(os.getenv("DASHBOARD_REFRESH", 5)),
            help="How often to poll Redis for new data"
        )
        threshold = st.number_input(
            "High spender threshold ($)",
            min_value=0,
            value=1000,
            step=100,
            help="Alert when user revenue exceeds this"
        )
        key_pattern = st.text_input(
            "Redis key pattern",
            value="user_analytics:*",
            help="Pattern to match analytics keys in Redis"
        )

        st.divider()
        if st.button("🔄 Force Refresh", type="primary"):
            st.cache_data.clear()
            st.rerun()

    # Get Redis client
    client = get_redis_client()

    # Fetch data with caching
    @st.cache_data(ttl=refresh_rate)
    def fetch_data(_client: redis.Redis, _pattern: str) -> pd.DataFrame:
        return get_redis_data(_client, _pattern)

    df = fetch_data(client, key_pattern)

    # Render dashboard
    render_metrics(df)
    st.divider()
    render_charts(df)
    st.divider()
    render_high_spenders(df, threshold)

    # Auto-refresh
    st.empty()  # Placeholder for spacing
    if st.button("⏱️ Auto-refresh enabled", disabled=True):
        pass
    st.caption(f"Auto-refreshing every {refresh_rate}s | Last updated: {pd.Timestamp.now():%H:%M:%S}")

    # Use streamlit_autorefresh for proper auto-refresh
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_rate * 1000, key="dashboard_refresh")
    except ImportError:
        logger.warning("streamlit_autorefresh not installed, manual refresh only")
        st.info("Install `streamlit-autorefresh` for automatic updates")


if __name__ == "__main__":
    main()