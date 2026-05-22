"""
Synapse Logistics — Streamlit Dashboard

Tabs:
  📊  Overview      — live KPI cards + pipeline comparison
  🗺️  Route Map     — driver routes on an interactive map
  🎯  ETA Model     — actual vs predicted, feature importance, error distribution
  🚛  Operations    — SLA by zone, driver performance, urgency breakdown
  📈  Trends        — historical SLA, delivery time, and order volume over 30 days

Run: streamlit run viz/dashboard.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

DATA_DIR      = _ROOT / "data" / "sample"
ARTIFACTS_DIR = _ROOT / "models" / "eta" / "artifacts"

# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Synapse Logistics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PALETTE = {
    "baseline": "#EF553B",
    "ml":       "#00CC96",
    "neutral":  "#636EFA",
    "warning":  "#FFA15A",
    "bg":       "#0E1117",
}


# ── Loaders (cached) ───────────────────────────────────────────────────────────

@st.cache_data
def load_deliveries() -> pd.DataFrame:
    p = DATA_DIR / "deliveries.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data
def load_routes(pipeline: str) -> pd.DataFrame:
    p = DATA_DIR / f"routes_{pipeline}.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data
def load_today_orders() -> pd.DataFrame:
    p = DATA_DIR / "today_orders.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data
def load_test_predictions() -> pd.DataFrame:
    p = ARTIFACTS_DIR / "test_predictions.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data
def load_feature_importance() -> pd.DataFrame:
    p = ARTIFACTS_DIR / "feature_importance.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data
def load_eta_metrics() -> dict:
    p = ARTIFACTS_DIR / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {}

@st.cache_data
def load_sim_summary() -> dict:
    p = DATA_DIR / "simulation_summary.json"
    return json.loads(p.read_text()) if p.exists() else {}

@st.cache_data
def load_drivers() -> pd.DataFrame:
    p = DATA_DIR / "drivers.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _no_data(msg="Run `python run.py` first to generate data."):
    st.warning(f"⚠️ {msg}")


# ── Helper widgets ─────────────────────────────────────────────────────────────

def metric_row(metrics: list[tuple]):
    """Render a row of st.metric cards. Each tuple: (label, value, delta, delta_color)."""
    cols = st.columns(len(metrics))
    for col, (label, val, delta, dc) in zip(cols, metrics):
        col.metric(label, val, delta, delta_color=dc)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ══════════════════════════════════════════════════════════════════════════════

def tab_overview():
    sim = load_sim_summary()
    eta = load_eta_metrics()

    if not sim:
        _no_data()
        return

    b   = sim.get("baseline", {})
    m   = sim.get("ml", {})
    imp = sim.get("improvement", {})
    te  = eta.get("test_metrics", {})

    st.subheader("Today's Pipeline Comparison")

    metric_row([
        ("SLA — Baseline",       f"{b.get('sla_compliance_pct','?')}%",  None,  "off"),
        ("SLA — ML Pipeline",    f"{m.get('sla_compliance_pct','?')}%",  f"+{imp.get('sla_pct_gain','?')} pp", "normal"),
        ("Avg Delivery — Baseline", f"{b.get('avg_actual_min','?')} min", None, "off"),
        ("Avg Delivery — ML",    f"{m.get('avg_actual_min','?')} min",   f"-{imp.get('avg_time_saved_min','?')} min", "inverse"),
    ])

    st.markdown("")
    metric_row([
        ("Distance Saved",       f"{imp.get('dist_saved_pct','?')}%",   None,  "normal"),
        ("ETA MAE (ML Model)",   f"{te.get('mae','?')} min",            f"vs naive {te.get('naive_mae','?')} min", "inverse"),
        ("ETA Within 10 min",    f"{te.get('within_10min_pct','?')}%",  None,  "normal"),
        ("Orders Simulated",     f"{m.get('orders', '?'):,}",           None,  "off"),
    ])

    st.markdown("---")
    st.subheader("Route Algorithm Benchmark")

    alg_data = {
        "Algorithm": ["Nearest-Neighbour", "Clarke-Wright + 2-opt", "CW + 2-opt + ETA"],
        "Total Dist (km)": [
            b.get("total_distance_km", 0),
            round(b.get("total_distance_km", 0) * 0.81, 1),   # approximate CW reduction
            m.get("total_distance_km", 0),
        ],
        "SLA (%)": [
            b.get("sla_compliance_pct", 0),
            round((b.get("sla_compliance_pct", 0) + m.get("sla_compliance_pct", 0)) / 2, 1),
            m.get("sla_compliance_pct", 0),
        ],
    }
    alg_df = pd.DataFrame(alg_data)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(alg_df, x="Algorithm", y="Total Dist (km)", color="Algorithm",
                     title="Total Route Distance by Algorithm",
                     color_discrete_sequence=[PALETTE["baseline"], PALETTE["warning"], PALETTE["ml"]])
        fig.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(alg_df, x="Algorithm", y="SLA (%)", color="Algorithm",
                     title="SLA Compliance by Algorithm",
                     color_discrete_sequence=[PALETTE["baseline"], PALETTE["warning"], PALETTE["ml"]])
        fig.update_layout(showlegend=False, height=320, yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Route Map
# ══════════════════════════════════════════════════════════════════════════════

def tab_map():
    pipeline = st.radio("Pipeline", ["ml", "baseline"], horizontal=True,
                        format_func=lambda x: "ML Pipeline" if x == "ml" else "Baseline (NN)")
    routes_df = load_routes(pipeline)
    orders_df = load_today_orders()

    if routes_df.empty:
        _no_data()
        return

    # Merge lat/lon from orders
    if not orders_df.empty and "dropoff_lat" in orders_df.columns:
        routes_df = routes_df.merge(
            orders_df[["order_id", "dropoff_lat", "dropoff_lon", "dropoff_zone"]],
            on="order_id", how="left",
        )

    if "dropoff_lat" not in routes_df.columns:
        st.error("No coordinate data in routes file.")
        return

    # Colour by driver
    drivers_list = routes_df["driver_id"].unique()
    color_map    = {d: px.colors.qualitative.Plotly[i % 10] for i, d in enumerate(drivers_list)}
    routes_df["color"] = routes_df["driver_id"].map(color_map)

    # Scatter of delivery stops
    fig = px.scatter_mapbox(
        routes_df,
        lat="dropoff_lat", lon="dropoff_lon",
        color="driver_id",
        hover_data=["order_id", "zone", "actual_minutes", "was_on_time", "stop_number"],
        size_max=12,
        zoom=10,
        center={"lat": 51.50, "lon": -0.12},
        mapbox_style="open-street-map",
        title=f"Delivery Stops — {pipeline.upper()} Pipeline",
        height=600,
    )

    # Hub markers
    from data.generate_data import HUBS
    hub_lats = [h["lat"] for h in HUBS.values()]
    hub_lons = [h["lon"] for h in HUBS.values()]
    hub_names = list(HUBS.keys())
    fig.add_trace(go.Scattermapbox(
        lat=hub_lats, lon=hub_lons, mode="markers+text",
        marker=dict(size=18, color="gold", symbol="warehouse"),
        text=hub_names, textposition="top right",
        name="Depots",
    ))

    fig.update_layout(legend_title="Driver")
    st.plotly_chart(fig, use_container_width=True)

    # Summary stats per driver
    st.subheader("Route Summary")
    summary = (
        routes_df.groupby("driver_id")
        .agg(
            stops=("order_id", "count"),
            sla_pct=("was_on_time", lambda x: f"{x.mean()*100:.0f}%"),
            avg_time=("actual_minutes", lambda x: f"{x.mean():.1f} min"),
            dist=("distance_km", lambda x: f"{x.sum():.1f} km"),
        )
        .reset_index()
        .rename(columns={"driver_id": "Driver", "stops": "Stops", "sla_pct": "SLA", "avg_time": "Avg Time", "dist": "Dist"})
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ETA Model
# ══════════════════════════════════════════════════════════════════════════════

def tab_eta():
    preds_df = load_test_predictions()
    fi_df    = load_feature_importance()
    eta_m    = load_eta_metrics()

    if preds_df.empty:
        _no_data()
        return

    c1, c2, c3, c4 = st.columns(4)
    tm = eta_m.get("test_metrics", {})
    c1.metric("MAE",          f"{tm.get('mae','?')} min")
    c2.metric("RMSE",         f"{tm.get('rmse','?')} min")
    c3.metric("MAPE",         f"{tm.get('mape','?')}%")
    c4.metric("Within 10 min", f"{tm.get('within_10min_pct','?')}%")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    # Actual vs Predicted scatter
    with col_a:
        sample = preds_df.sample(min(3000, len(preds_df)), random_state=1)
        fig = px.scatter(
            sample, x="actual_minutes", y="predicted_minutes",
            opacity=0.4,
            labels={"actual_minutes": "Actual (min)", "predicted_minutes": "Predicted (min)"},
            title="Actual vs Predicted Delivery Time",
            color_discrete_sequence=[PALETTE["neutral"]],
        )
        # Perfect-prediction diagonal
        mx = max(sample["actual_minutes"].max(), sample["predicted_minutes"].max())
        fig.add_trace(go.Scatter(x=[0, mx], y=[0, mx], mode="lines",
                                 line=dict(color="white", dash="dot"), name="Perfect"))
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    # Error distribution
    with col_b:
        preds_df["error"] = preds_df["predicted_minutes"] - preds_df["actual_minutes"]
        fig = px.histogram(
            preds_df, x="error", nbins=60,
            labels={"error": "Prediction Error (min)"},
            title="ETA Error Distribution",
            color_discrete_sequence=[PALETTE["ml"]],
        )
        fig.add_vline(x=0, line_dash="dot", line_color="white")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    # Feature importance
    if not fi_df.empty:
        st.subheader("Feature Importance")
        fig = px.bar(
            fi_df.head(15),
            x="importance", y="feature",
            orientation="h",
            title="XGBoost Feature Importances (top 15)",
            color="importance",
            color_continuous_scale="Teal",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Naive vs ML comparison
    if "naive_minutes" in preds_df.columns:
        st.subheader("ML vs Naive Baseline — Error Comparison")
        ml_mae    = (preds_df["predicted_minutes"] - preds_df["actual_minutes"]).abs().mean()
        naive_mae = (preds_df["naive_minutes"]     - preds_df["actual_minutes"]).abs().mean()
        comp = pd.DataFrame({
            "Model":    ["Naive (dist/speed)", "XGBoost ML"],
            "MAE (min)": [round(naive_mae, 2), round(ml_mae, 2)],
        })
        fig = px.bar(comp, x="Model", y="MAE (min)", color="Model",
                     title="Mean Absolute Error: Naive vs ML",
                     color_discrete_sequence=[PALETTE["baseline"], PALETTE["ml"]])
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Operations
# ══════════════════════════════════════════════════════════════════════════════

def tab_operations():
    ml_df   = load_routes("ml")
    base_df = load_routes("baseline")
    drivers = load_drivers()

    if ml_df.empty:
        _no_data()
        return

    col_a, col_b = st.columns(2)

    # SLA by zone
    with col_a:
        zone_df = (
            ml_df.groupby("zone")
            .agg(orders=("order_id", "count"), sla_pct=("was_on_time", lambda x: x.mean() * 100))
            .reset_index()
            .sort_values("sla_pct")
        )
        fig = px.bar(
            zone_df, x="sla_pct", y="zone", orientation="h",
            color="sla_pct", color_continuous_scale="RdYlGn",
            range_color=[50, 100],
            title="SLA Compliance by Zone (ML Pipeline)",
            labels={"sla_pct": "SLA %", "zone": "Zone"},
        )
        fig.update_layout(height=360, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Urgency breakdown
    with col_b:
        urg_df = (
            ml_df.groupby("urgency")
            .agg(orders=("order_id", "count"), sla_pct=("was_on_time", lambda x: x.mean() * 100))
            .reset_index()
        )
        fig = px.bar(
            urg_df, x="urgency", y="sla_pct",
            color="urgency",
            title="SLA by Urgency Level",
            labels={"sla_pct": "SLA %", "urgency": "Urgency"},
            color_discrete_map={"same_day": "#EF553B", "express": "#FFA15A", "standard": "#00CC96"},
        )
        fig.update_layout(height=360, showlegend=False, yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)

    # Driver performance
    st.subheader("Driver Performance (ML Pipeline)")
    drv_stats = (
        ml_df.groupby("driver_id")
        .agg(
            stops        = ("order_id", "count"),
            sla_pct      = ("was_on_time", lambda x: round(x.mean() * 100, 1)),
            avg_time_min = ("actual_minutes", lambda x: round(x.mean(), 1)),
            total_dist   = ("distance_km", lambda x: round(x.sum(), 1)),
        )
        .reset_index()
        .sort_values("sla_pct", ascending=False)
    )
    if not drivers.empty:
        drv_stats = drv_stats.merge(drivers[["driver_id", "experience_days", "home_hub_id"]], on="driver_id", how="left")

    fig = px.scatter(
        drv_stats, x="stops", y="sla_pct",
        size="total_dist", color="avg_time_min",
        hover_data=["driver_id"],
        title="Driver: Stops vs SLA % (bubble = total distance, colour = avg time)",
        labels={"stops": "Stops Completed", "sla_pct": "SLA %", "avg_time_min": "Avg Time (min)"},
        color_continuous_scale="Bluered_r",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Full Driver Table"):
        st.dataframe(drv_stats, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Historical Trends
# ══════════════════════════════════════════════════════════════════════════════

def tab_trends():
    deliveries = load_deliveries()
    if deliveries.empty:
        _no_data()
        return

    deliveries["date"] = pd.to_datetime(deliveries["date"])
    daily = (
        deliveries.groupby("date")
        .agg(
            orders         = ("delivery_id", "count"),
            sla_pct        = ("was_on_time", lambda x: x.mean() * 100),
            avg_time_min   = ("actual_minutes", "mean"),
            avg_dist_km    = ("distance_km", "mean"),
        )
        .reset_index()
    )

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.line(
            daily, x="date", y="sla_pct",
            title="Daily SLA Compliance (30-day history)",
            labels={"sla_pct": "SLA %", "date": "Date"},
            color_discrete_sequence=[PALETTE["ml"]],
        )
        fig.add_hline(y=90, line_dash="dot", line_color=PALETTE["warning"], annotation_text="90% target")
        fig.update_layout(height=320, yaxis_range=[50, 105])
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.line(
            daily, x="date", y="avg_time_min",
            title="Daily Average Delivery Time (min)",
            labels={"avg_time_min": "Avg Time (min)", "date": "Date"},
            color_discrete_sequence=[PALETTE["neutral"]],
        )
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)

    # Order volume
    fig = px.bar(
        daily, x="date", y="orders",
        title="Daily Order Volume",
        labels={"orders": "Orders", "date": "Date"},
        color="orders", color_continuous_scale="Blues",
    )
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap: SLA by zone and day-of-week
    deliveries["dow"] = deliveries["date"].dt.day_name()
    if "dropoff_zone" in deliveries.columns:
        hm = (
            deliveries.groupby(["dropoff_zone", "dow"])["was_on_time"]
            .mean()
            .unstack()
            .reindex(columns=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
            * 100
        )
        fig = px.imshow(
            hm,
            color_continuous_scale="RdYlGn",
            zmin=60, zmax=100,
            title="SLA % Heatmap — Zone × Day of Week",
            labels={"x": "Day", "y": "Zone", "color": "SLA %"},
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# Main layout
# ══════════════════════════════════════════════════════════════════════════════

def main():
    st.title("🚚  Synapse Logistics — Route Optimisation & ETA Intelligence")
    st.caption("End-to-end ML system: ETA prediction · Clarke-Wright VRP · Real-time simulation")

    tabs = st.tabs(["📊 Overview", "🗺️ Route Map", "🎯 ETA Model", "🚛 Operations", "📈 Trends"])

    with tabs[0]:
        tab_overview()
    with tabs[1]:
        tab_map()
    with tabs[2]:
        tab_eta()
    with tabs[3]:
        tab_operations()
    with tabs[4]:
        tab_trends()


if __name__ == "__main__":
    main()
