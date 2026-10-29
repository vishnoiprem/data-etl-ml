"""
digest.py — pure functions that shape the digest's data.

Kept separate from the Streamlit `app.py` so the shaping
logic is unit-testable: feed a DataFrame in, get the
metrics out, no Streamlit / Spark dependency.

The Streamlit app calls these directly:

    from m100.digest import compute_metrics, filter_recent
    summary = compute_metrics(iter_df, log_df)
    recent = filter_recent(iter_df, n=20)
    st.metric("Iterations run", summary["n_iterations"])

What we compute:

  * `compute_metrics(iter_df, log_df)` — top-line numbers
    for the header strip (n_iters, n_ok, n_skipped,
    n_failed, total_tokens, avg_quality, median_quality,
    total_cost_usd, n_distinct_categories, n_distinct_listings).
  * `filter_recent(iter_df, n=20)` — last N rows by iter_no,
    sorted descending, with a stable subset of fields.
  * `category_breakdown(iter_df)` — category → count dict
    for the bar chart.
  * `quality_timeline(iter_df)` — iter_no → quality_score
    dict for the line chart.
  * `digest_golden(iter_df, log_df, seed=42)` — builds a
    deterministic "golden" digest snapshot for the
    regression test. Two runs with the same input produce
    the same byte-for-byte output (modulo wall-clock).
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from typing import Any, Optional


# ============================================================
# Top-line metrics
# ============================================================

def compute_metrics(
    iter_df: Any,
    log_df: Optional[Any] = None,
    cost_usd_total: float = 0.0,
) -> dict:
    """Top-line numbers for the digest header strip.

    `iter_df` and `log_df` are pandas DataFrames (the
    Streamlit app passes `spark.read.table(...).toPandas()`).
    Anything with the same `.columns` interface works.
    """
    n = len(iter_df)
    if n == 0:
        return {
            "n_iterations": 0,
            "n_ok": 0,
            "n_skipped": 0,
            "n_failed": 0,
            "n_distinct_categories": 0,
            "n_distinct_listings": 0,
            "total_tokens": 0,
            "total_cost_usd": round(cost_usd_total, 6),
            "avg_quality": 0.0,
            "median_quality": 0.0,
            "quality_min": 0.0,
            "quality_max": 0.0,
        }

    statuses = Counter(iter_df["status"])
    qualities = iter_df["quality_score"].fillna(0).tolist()

    total_tokens = 0
    if log_df is not None and len(log_df) > 0:
        total_tokens = int(
            log_df["prompt_tokens"].fillna(0).sum()
            + log_df["completion_tokens"].fillna(0).sum()
        )

    return {
        "n_iterations": n,
        "n_ok": int(statuses.get("ok", 0)),
        "n_skipped": int(statuses.get("skipped", 0)),
        "n_failed": int(statuses.get("failed", 0)),
        "n_distinct_categories": int(iter_df["category"].nunique()),
        "n_distinct_listings": int(iter_df["listing_id"].nunique()),
        "total_tokens": total_tokens,
        "total_cost_usd": round(cost_usd_total, 6),
        "avg_quality": round(statistics.mean(qualities), 4) if qualities else 0,
        "median_quality": round(statistics.median(qualities), 4) if qualities else 0,
        "quality_min": round(min(qualities), 4) if qualities else 0,
        "quality_max": round(max(qualities), 4) if qualities else 0,
    }


# ============================================================
# Recent rows
# ============================================================

# The columns shown in the "Latest agent summaries" table.
SUMMARY_COLS = [
    "iter_no", "category", "listing_id", "status",
    "quality_score", "summary",
]


def filter_recent(iter_df: Any, n: int = 20) -> Any:
    """Return the last N iterations, sorted by iter_no DESC.

    Only the columns we display in the digest table.
    """
    if len(iter_df) == 0:
        return iter_df
    cols = [c for c in SUMMARY_COLS if c in iter_df.columns]
    return (
        iter_df[cols]
        .sort_values("iter_no", ascending=False)
        .head(n)
    )


# ============================================================
# Charts
# ============================================================

def category_breakdown(iter_df: Any) -> dict[str, int]:
    """category → count, sorted by count DESC."""
    if len(iter_df) == 0 or "category" not in iter_df.columns:
        return {}
    counts = iter_df["category"].value_counts()
    return {str(k): int(v) for k, v in counts.items()}


def quality_timeline(iter_df: Any) -> dict[int, float]:
    """iter_no → quality_score, sorted by iter_no ASC."""
    if len(iter_df) == 0:
        return {}
    pairs = (
        iter_df[["iter_no", "quality_score"]]
        .dropna()
        .sort_values("iter_no")
        .itertuples(index=False, name=None)
    )
    return {int(it): float(q) for it, q in pairs}


# ============================================================
# Golden digest — deterministic regression test
# ============================================================

def digest_golden(iter_df: Any, log_df: Optional[Any] = None) -> str:
    """Produce a deterministic JSON digest for a given input.

    Two runs with the same input produce byte-for-byte
    identical output (we sort all keys). Wall-clock fields
    are excluded.
    """
    summary = compute_metrics(iter_df, log_df)
    payload = {
        "summary": summary,
        "category_breakdown": category_breakdown(iter_df),
        "quality_timeline": quality_timeline(iter_df),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import pandas as pd

    # Demo: build a 5-row synthetic frame, print the digest
    df = pd.DataFrame([
        {"iter_no": 0, "listing_id": "l0", "category": "Finance",
         "status": "ok", "quality_score": 0.5, "summary": "..."},
        {"iter_no": 1, "listing_id": "l1", "category": "Healthcare",
         "status": "ok", "quality_score": 0.7, "summary": "..."},
        {"iter_no": 2, "listing_id": "l2", "category": "Geospatial",
         "status": "skipped", "quality_score": 0.3, "summary": "..."},
        {"iter_no": 3, "listing_id": "l3", "category": "Retail",
         "status": "ok", "quality_score": 0.85, "summary": "..."},
        {"iter_no": 4, "listing_id": "l4", "category": "Energy",
         "status": "failed", "quality_score": 0.1, "summary": "..."},
    ])
    print(digest_golden(df))