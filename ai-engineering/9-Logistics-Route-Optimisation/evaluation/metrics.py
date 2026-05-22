"""
Evaluation & Reporting

Computes all operational KPIs and prints a formatted report card.

Metrics:
  ETA Model  — MAE, RMSE, MAPE, within-5-min %, within-10-min %
  Routing    — algorithm comparison table (distance / time saved)
  Simulation — SLA compliance, avg delivery time, driver utilisation
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

DATA_DIR      = _ROOT / "data" / "sample"
ARTIFACTS_DIR = _ROOT / "models" / "eta" / "artifacts"


# ── ETA model metrics ──────────────────────────────────────────────────────────

def eta_metrics() -> dict:
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    if not metrics_path.exists():
        return {}
    with open(metrics_path) as f:
        return json.load(f)


# ── SLA / operational metrics ──────────────────────────────────────────────────

def simulation_metrics() -> dict:
    summary_path = DATA_DIR / "simulation_summary.json"
    if not summary_path.exists():
        return {}
    with open(summary_path) as f:
        return json.load(f)


def sla_by_zone(pipeline: str = "ml") -> pd.DataFrame:
    fpath = DATA_DIR / f"routes_{pipeline}.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath)
    return (
        df.groupby("zone")
        .agg(
            orders=("order_id", "count"),
            sla_pct=("was_on_time", lambda x: round(x.mean() * 100, 1)),
            avg_time=("actual_minutes", lambda x: round(x.mean(), 1)),
        )
        .reset_index()
        .sort_values("sla_pct")
    )


def driver_performance(pipeline: str = "ml") -> pd.DataFrame:
    fpath = DATA_DIR / f"routes_{pipeline}.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath)
    return (
        df.groupby("driver_id")
        .agg(
            stops=("order_id", "count"),
            sla_pct=("was_on_time", lambda x: round(x.mean() * 100, 1)),
            avg_time=("actual_minutes", lambda x: round(x.mean(), 1)),
            total_dist=("distance_km", "sum"),
        )
        .reset_index()
        .sort_values("sla_pct", ascending=False)
    )


# ── Routing comparison ─────────────────────────────────────────────────────────

def routing_comparison(orders_df: pd.DataFrame, drivers_df: pd.DataFrame, traffic_df: pd.DataFrame) -> pd.DataFrame:
    from models.routing.optimizer import RoutingOptimizer
    try:
        from models.eta.predict import predict_eta
        eta_fn = predict_eta
    except Exception:
        eta_fn = None

    opt = RoutingOptimizer(eta_model_fn=eta_fn)
    return opt.compare_algorithms(orders_df, drivers_df, traffic_df, current_hour=9)


# ── Report card ────────────────────────────────────────────────────────────────

def print_report_card():
    LINE = "═" * 66

    print(f"\n  {LINE}")
    print(f"  {'SYNAPSE LOGISTICS — PERFORMANCE REPORT CARD':^66}")
    print(f"  {LINE}")

    # ETA model
    eta = eta_metrics()
    if eta:
        tm = eta.get("test_metrics", {})
        print(f"\n  {'ETA PREDICTION MODEL':}")
        print(f"  {'─' * 40}")
        print(f"    Model          : {eta.get('model_name', 'Unknown')}")
        print(f"    Train samples  : {eta.get('n_train', 0):,}")
        print(f"    Test samples   : {eta.get('n_test', 0):,}")
        print(f"    MAE            : {tm.get('mae', '?')} min")
        print(f"    RMSE           : {tm.get('rmse', '?')} min")
        print(f"    MAPE           : {tm.get('mape', '?')} %")
        print(f"    Within  5 min  : {tm.get('within_5min_pct', '?')} %")
        print(f"    Within 10 min  : {tm.get('within_10min_pct', '?')} %")
        if "naive_mae" in tm:
            print(f"    Naive baseline : {tm['naive_mae']} min  →  ML gain: {tm.get('improvement_pct', '?')}%")

    # Simulation
    sim = simulation_metrics()
    if sim:
        b = sim.get("baseline", {})
        m = sim.get("ml", {})
        imp = sim.get("improvement", {})
        print(f"\n  {'DELIVERY SIMULATION (TODAY)':}")
        print(f"  {'─' * 40}")
        print(f"    {'Metric':<28} {'Baseline':>10} {'ML':>10} {'Δ':>8}")
        print(f"    {'·' * 58}")
        print(f"    {'SLA compliance (%)':<28} {b.get('sla_compliance_pct','?'):>9}% {m.get('sla_compliance_pct','?'):>9}%  {'+' if (imp.get('sla_pct_gain') or 0)>=0 else ''}{imp.get('sla_pct_gain','?')} pp")
        print(f"    {'Avg delivery time (min)':<28} {b.get('avg_actual_min','?'):>10} {m.get('avg_actual_min','?'):>10}  -{imp.get('avg_time_saved_min','?')} min")
        print(f"    {'Total distance (km)':<28} {b.get('total_distance_km','?'):>10} {m.get('total_distance_km','?'):>10}  {imp.get('dist_saved_pct','?')}% saved")
        print(f"    {'Avg ETA error (min)':<28} {b.get('avg_eta_error_min','?'):>10} {m.get('avg_eta_error_min','?'):>10}")

    # Zone SLA
    zone_df = sla_by_zone("ml")
    if not zone_df.empty:
        print(f"\n  {'SLA BY ZONE (ML PIPELINE)':}")
        print(f"  {'─' * 40}")
        print(f"    {'Zone':<12} {'Orders':>8} {'SLA %':>8} {'Avg Time':>10}")
        print(f"    {'·' * 42}")
        for _, row in zone_df.iterrows():
            bar = "▓" * int(row["sla_pct"] / 10)
            print(f"    {row['zone']:<12} {int(row['orders']):>8} {row['sla_pct']:>7.1f}%  {bar}")

    print(f"\n  {LINE}\n")


if __name__ == "__main__":
    print_report_card()
