"""
End-to-End Delivery Day Simulator

Compares two pipelines on today's orders:

  BASELINE — Nearest-Neighbour routing + naive ETA estimate (distance / speed)
  ML       — CW + 2-opt + ETA-guided routing + XGBoost ETA prediction

Outputs:
  data/sample/simulation_results.csv   — per-order comparison
  data/sample/routes_ml.csv            — ML route assignments
  data/sample/routes_baseline.csv      — baseline route assignments
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from data.generate_data import HUBS, haversine, BASE_SPEED_KMH
from models.routing.optimizer import Route, RoutingOptimizer, Stop

DATA_DIR   = _ROOT / "data" / "sample"
OUTPUT_DIR = DATA_DIR


# ── Simulate one route ─────────────────────────────────────────────────────────

def _simulate_route(
    route: Route,
    traffic_lookup: dict,
    rng: np.random.Generator,
    eta_fn=None,
    weather: float = 0.0,
) -> List[dict]:
    """Walk through a route stop-by-stop, compute actual vs predicted delivery times."""
    if not route.stops:
        return []

    hub = HUBS[route.hub_id]
    cur_lat, cur_lon = hub["lat"], hub["lon"]
    cur_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

    route_start_time = cur_time   # when driver departs hub — SLA measured from here

    records = []
    for stop_num, stop in enumerate(route.stops):
        dist_km  = haversine(cur_lat, cur_lon, stop.lat, stop.lon)
        hour     = cur_time.hour
        cong     = traffic_lookup.get((stop.zone, hour), 0.40)

        # ── Actual delivery time ───────────────────────────────────────────────
        wx_factor  = 1 - 0.30 * weather
        eff_speed  = max(BASE_SPEED_KMH * (1 - 0.75 * cong) * wx_factor, 5.0)
        travel_min = (dist_km / eff_speed) * 60
        stop_min   = rng.uniform(3, 8)
        noise      = rng.normal(0, travel_min * 0.12)
        actual_min = max(travel_min + stop_min + noise, 2.0)

        # ── Predicted delivery time ────────────────────────────────────────────
        if eta_fn is not None:
            feat_row = pd.DataFrame([{
                "distance_km":        dist_km,
                "hub_to_dropoff_km":  dist_km * 1.1,
                "hour_of_day":        hour,
                "day_of_week":        cur_time.weekday(),
                "is_weekend":         int(cur_time.weekday() >= 5),
                "is_peak_hour":       int(7 <= hour <= 9 or 17 <= hour <= 19),
                "zone_id":            0,
                "hub_id_enc":         0,
                "congestion_at_time": cong,
                "weather_severity":   weather,
                "package_weight_kg":  stop.weight_kg,
                "stop_number":        stop_num,
                "log_experience":     np.log1p(365),
                "speed_factor":       1.0,
                "urgency_enc":        {"same_day": 2, "express": 1, "standard": 0}.get(stop.urgency, 0),
            }])
            predicted_min = float(eta_fn(feat_row)[0])
        else:
            predicted_min = (dist_km / BASE_SPEED_KMH) * 60 + 5.0  # naive

        arrival_time = cur_time + timedelta(minutes=actual_min)
        eta_error = abs(actual_min - predicted_min)

        # SLA = cumulative time since driver left the hub (realistic "promised window")
        mins_since_order = (arrival_time - route_start_time).total_seconds() / 60
        was_on_time = mins_since_order <= stop.sla_minutes

        records.append({
            "order_id":              stop.order_id,
            "driver_id":             route.driver_id,
            "hub_id":                route.hub_id,
            "stop_number":           stop_num,
            "zone":                  stop.zone,
            "urgency":               stop.urgency,
            "sla_minutes":           stop.sla_minutes,
            "distance_km":           round(dist_km, 3),
            "congestion":            round(cong, 3),
            "actual_minutes":        round(actual_min, 1),
            "mins_since_order":      round(mins_since_order, 1),
            "predicted_minutes":     round(predicted_min, 1),
            "eta_error_minutes":     round(eta_error, 1),
            "was_on_time":           was_on_time,
            "dispatch_time":         cur_time.isoformat(),
        })

        cur_lat, cur_lon = stop.lat, stop.lon
        cur_time += timedelta(minutes=actual_min)

    return records


# ── Main simulation ────────────────────────────────────────────────────────────

def run_simulation(verbose: bool = True) -> dict:
    rng = np.random.default_rng(99)

    orders  = pd.read_csv(DATA_DIR / "today_orders.csv")
    drivers = pd.read_csv(DATA_DIR / "drivers.csv")
    traffic = pd.read_csv(DATA_DIR / "today_traffic.csv")

    # Traffic lookup at dispatch hour (9 am)
    HOUR = 9
    tlookup = {(r.zone, r.hour): r.congestion_level for r in traffic[traffic.hour == HOUR].itertuples()}

    # Try to load ETA model
    try:
        from models.eta.predict import predict_eta as _eta_fn
        eta_fn = _eta_fn
        has_eta = True
    except FileNotFoundError:
        eta_fn = None
        has_eta = False

    opt = RoutingOptimizer(eta_model_fn=eta_fn)

    # ── Baseline: NN routes + naive ETA ───────────────────────────────────────
    base_routes: Dict[str, Route] = opt.optimize(orders, drivers, traffic, mode="nn", current_hour=HOUR)
    base_records = []
    for route in base_routes.values():
        base_records.extend(_simulate_route(route, tlookup, rng, eta_fn=None))
    base_df = pd.DataFrame(base_records)

    # ── ML pipeline: CW + 2-opt + ETA reorder ─────────────────────────────────
    ml_mode = "eta" if has_eta else "cw"
    ml_routes: Dict[str, Route] = opt.optimize(orders, drivers, traffic, mode=ml_mode, current_hour=HOUR)
    ml_records = []
    for route in ml_routes.values():
        ml_records.extend(_simulate_route(route, tlookup, rng, eta_fn=eta_fn))
    ml_df = pd.DataFrame(ml_records)

    # ── Comparison ─────────────────────────────────────────────────────────────
    def _kpis(df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        time_col = "mins_since_order" if "mins_since_order" in df.columns else "actual_minutes"
        return {
            "orders":             len(df),
            "sla_compliance_pct": round(df["was_on_time"].mean() * 100, 1),
            "avg_actual_min":     round(df[time_col].mean(), 1),
            "avg_eta_error_min":  round(df["eta_error_minutes"].mean(), 1),
            "total_distance_km":  round(df["distance_km"].sum(), 1),
            "avg_dist_per_order": round(df["distance_km"].mean(), 3),
        }

    results = {
        "baseline": _kpis(base_df),
        "ml":       _kpis(ml_df),
        "has_eta_model": has_eta,
    }

    if results["baseline"] and results["ml"]:
        b, m = results["baseline"], results["ml"]
        results["improvement"] = {
            "sla_pct_gain":       round(m["sla_compliance_pct"] - b["sla_compliance_pct"], 1),
            "avg_time_saved_min": round(b["avg_actual_min"] - m["avg_actual_min"], 1),
            "dist_saved_pct":     round((1 - m["total_distance_km"] / max(b["total_distance_km"], 0.01)) * 100, 1),
            "eta_error_reduction_min": round(b["avg_eta_error_min"] - m["avg_eta_error_min"], 1) if has_eta else None,
        }

    # ── Save outputs ───────────────────────────────────────────────────────────
    if not base_df.empty:
        base_df.to_csv(OUTPUT_DIR / "routes_baseline.csv", index=False)
    if not ml_df.empty:
        ml_df.to_csv(OUTPUT_DIR / "routes_ml.csv", index=False)

    # Combined comparison
    if not base_df.empty and not ml_df.empty:
        base_df["pipeline"] = "baseline"
        ml_df["pipeline"]   = "ml"
        pd.concat([base_df, ml_df]).to_csv(OUTPUT_DIR / "simulation_results.csv", index=False)

    with open(OUTPUT_DIR / "simulation_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    if verbose:
        b, m = results.get("baseline", {}), results.get("ml", {})
        print(f"\n  {'Metric':<32} {'Baseline':>12} {'ML Pipeline':>14} {'Δ':>8}")
        print(f"  {'─' * 70}")
        if b and m:
            imp = results.get("improvement", {})
            print(f"  {'Orders processed':<32} {b['orders']:>12,} {m['orders']:>14,}")
            print(f"  {'SLA compliance (%)':<32} {b['sla_compliance_pct']:>11.1f}% {m['sla_compliance_pct']:>13.1f}%  {'+' if imp.get('sla_pct_gain',0)>=0 else ''}{imp.get('sla_pct_gain','N/A')} pp")
            print(f"  {'Avg delivery time (min)':<32} {b['avg_actual_min']:>12.1f} {m['avg_actual_min']:>14.1f}  {'-'+str(imp.get('avg_time_saved_min',''))} min")
            print(f"  {'Total distance (km)':<32} {b['total_distance_km']:>12.1f} {m['total_distance_km']:>14.1f}  {imp.get('dist_saved_pct','N/A')}% saved")
            print(f"  {'Avg ETA error (min)':<32} {b['avg_eta_error_min']:>12.1f} {m['avg_eta_error_min']:>14.1f}")

    return results


if __name__ == "__main__":
    run_simulation()
