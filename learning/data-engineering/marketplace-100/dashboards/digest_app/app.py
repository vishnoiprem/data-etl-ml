"""
digest_app/app.py — Streamlit app for the Marketplace 100 digest.

Reads the iterations Delta table + Lakebase ops log and shows
the running digest: per-iteration quality scores, token spend,
retries, and a category mix pie. Deployable as a Databricks
App via DAB (resources/apps/databricks_app.yml).

Run locally:
    streamlit run dashboards/digest_app/app.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Make `m100` importable when running via `streamlit run ...`
# from the repo root (without `pip install -e .`).
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_REPO, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import pandas as pd
import streamlit as st

from m100.digest import (
    compute_metrics,
    filter_recent,
    category_breakdown,
    quality_timeline,
    SUMMARY_COLS,
)


# ============================================================
# Config
# ============================================================

CATALOG = os.getenv("M100_CATALOG", "marketplace_100")
ITER_TABLE = f"{CATALOG}.agents.iterations"
AGENT_LOG_TABLE = f"{CATALOG}.agents.lakebase_fallback"


# ============================================================
# Data loaders — Databricks SQL or local delta
# ============================================================

@st.cache_data(ttl=30)
def load_iterations() -> pd.DataFrame:
    """Read the iterations Delta table. Cached for 30s."""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        df = spark.read.table(ITER_TABLE).toPandas()
    except Exception:
        # Local fallback: empty DataFrame
        df = pd.DataFrame(columns=[
            "iter_no", "listing_id", "category", "status", "bronze_table",
            "silver_table", "gold_table", "mlflow_run_id", "model_name",
            "quality_score", "next_category", "summary", "retry_count",
            "duration_seconds", "started_at", "finished_at",
        ])
    return df


@st.cache_data(ttl=30)
def load_agent_log() -> pd.DataFrame:
    """Read the agent ops log."""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        df = spark.read.table(AGENT_LOG_TABLE).toPandas()
    except Exception:
        df = pd.DataFrame(columns=[
            "kind", "iter_no", "listing_id", "status", "quality_score",
            "prompt_tokens", "completion_tokens", "latency_ms", "summary",
            "raw_json", "created_at",
        ])
    return df


# ============================================================
# UI
# ============================================================

st.set_page_config(
    page_title="Marketplace 100 — Live Digest",
    layout="wide",
    page_icon="🌀",
)
st.title("🌀 Marketplace 100 — live digest")
st.caption(
    "100 marketplace datasets. 1 self-driving agent. "
    "Zero Airflow. Updated every 30s."
)

iter_df = load_iterations()
log_df = load_agent_log()

if iter_df.empty:
    st.info("No iterations yet. Trigger the driver Job from the Databricks Workflows page.")
    st.stop()

# ---- top metrics row ------------------------------------------------
# All shaping logic lives in m100.digest so it's unit-testable.
m = compute_metrics(iter_df, log_df)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Iterations run", m["n_iterations"])
col2.metric("OK", m["n_ok"])
col3.metric("Skipped", m["n_skipped"])
col4.metric("Failed", m["n_failed"])
col5.metric("LLM tokens", f"{m['total_tokens']:,}")

# ---- quality-score timeline -----------------------------------------
st.subheader("Quality score per iteration")
timeline = quality_timeline(iter_df)
if timeline:
    timeline_df = pd.DataFrame(
        [(k, v) for k, v in timeline.items()],
        columns=["iter_no", "quality_score"],
    ).set_index("iter_no")
    st.line_chart(timeline_df, y="quality_score", height=240)

# ---- category mix ----------------------------------------------------
st.subheader("Category mix")
cats = category_breakdown(iter_df)
if cats:
    cat_df = pd.DataFrame(
        [(k, v) for k, v in cats.items()],
        columns=["category", "count"],
    ).set_index("category")
    st.bar_chart(cat_df, height=240)

# ---- agent summaries -------------------------------------------------
st.subheader("Latest agent summaries")
recent = filter_recent(iter_df, n=20)
if not recent.empty:
    st.dataframe(recent, use_container_width=True, hide_index=True)

# ---- agent log (token spend) ----------------------------------------
st.subheader("Agent ops log (last 20)")
if not log_df.empty:
    log_show = log_df[[
        "iter_no", "listing_id", "prompt_tokens", "completion_tokens",
        "latency_ms", "quality_score", "summary",
    ]].sort_values("iter_no", ascending=False).head(20)
    st.dataframe(log_show, use_container_width=True, hide_index=True)
else:
    st.info("No agent log rows yet (Lakebase writes happen per iteration).")

# ---- footer ----------------------------------------------------------
st.caption(
    f"Last refreshed: {datetime.now(timezone.utc).isoformat(timespec='seconds')}  •  "
    f"Catalog: `{CATALOG}`  •  Iterations table: `{ITER_TABLE}`"
)
