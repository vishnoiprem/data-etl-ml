"""
Feature engineering pipeline for ETA prediction.

Takes raw delivery + order + driver records and produces a
model-ready feature matrix with 15 predictors.

Features:
  Spatial   : distance_km, hub_to_dropoff_km, zone_id, hub_id_enc
  Temporal  : hour_of_day, day_of_week, is_weekend, is_peak_hour
  Traffic   : congestion_at_time, weather_severity
  Package   : package_weight_kg, urgency_enc
  Route     : stop_number
  Driver    : log_experience, speed_factor
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from data.generate_data import HUBS, ZONE_IDS, HUB_IDS, haversine

DATA_DIR   = _ROOT / "data" / "sample"
OUTPUT_DIR = DATA_DIR

# ── Column registry ────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "distance_km",
    "hub_to_dropoff_km",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_peak_hour",
    "zone_id",
    "hub_id_enc",
    "congestion_at_time",
    "weather_severity",
    "package_weight_kg",
    "stop_number",
    "log_experience",
    "speed_factor",
    "urgency_enc",
]
TARGET_COL = "actual_minutes"
ID_COLS    = ["delivery_id", "order_id", "date"]


# ── Feature extractors ─────────────────────────────────────────────────────────

def _time_features(df: pd.DataFrame) -> pd.DataFrame:
    time_col = "dispatch_time" if "dispatch_time" in df.columns else "order_time"
    dt = pd.to_datetime(df[time_col], format="ISO8601", utc=False)
    df = df.copy()
    df["hour_of_day"] = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek
    df["is_weekend"]  = (dt.dt.dayofweek >= 5).astype(int)
    df["is_peak_hour"] = (
        ((dt.dt.hour >= 7)  & (dt.dt.hour <= 9)) |
        ((dt.dt.hour >= 17) & (dt.dt.hour <= 19))
    ).astype(int)
    return df


def _spatial_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Straight-line distance pickup → dropoff
    if all(c in df.columns for c in ["pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon"]):
        df["distance_km"] = df.apply(
            lambda r: haversine(r["pickup_lat"], r["pickup_lon"],
                                r["dropoff_lat"], r["dropoff_lon"]),
            axis=1,
        )
    elif "distance_km" not in df.columns:
        df["distance_km"] = 2.0

    # Hub → dropoff distance
    def _hub_dist(row):
        hub = HUBS.get(row.get("hub_id", ""), {})
        if hub and "dropoff_lat" in row:
            return haversine(hub["lat"], hub["lon"], row["dropoff_lat"], row["dropoff_lon"])
        return row.get("distance_km", 2.0)

    df["hub_to_dropoff_km"] = df.apply(_hub_dist, axis=1)

    # Categorical encodings
    df["zone_id"]    = df.get("dropoff_zone",    pd.Series(["CENTRAL"] * len(df))).map(ZONE_IDS).fillna(0).astype(int)
    df["hub_id_enc"] = df.get("hub_id",          pd.Series(["hub_central"] * len(df))).map(HUB_IDS).fillna(0).astype(int)

    return df


def _driver_features(df: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "driver_id" in df.columns and not drivers.empty:
        feats = drivers[["driver_id", "experience_days", "speed_factor"]].copy()
        feats["log_experience"] = np.log1p(feats["experience_days"])
        df = df.merge(feats, on="driver_id", how="left", suffixes=("", "_drv"))
    else:
        # Fallback: use columns that may already be in deliveries
        df["experience_days"] = df.get("driver_experience_days", pd.Series(365, index=df.index))
        df["speed_factor"]    = df.get("driver_speed_factor",    pd.Series(1.0,  index=df.index))
        df["log_experience"]  = np.log1p(df["experience_days"].fillna(365))
    return df


def _package_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    urg_map = {"same_day": 2, "express": 1, "standard": 0}
    df["urgency_enc"] = df.get("urgency", pd.Series("standard", index=df.index)).map(urg_map).fillna(0).astype(int)
    return df


# ── Full pipeline ──────────────────────────────────────────────────────────────

def build_feature_matrix(
    deliveries: pd.DataFrame,
    orders: pd.DataFrame,
    drivers: pd.DataFrame,
) -> pd.DataFrame:
    """Join, extract, and select all features. Returns model-ready DataFrame."""
    # Merge order spatial/package info into deliveries
    order_cols = ["order_id", "pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon",
                  "package_weight_kg", "urgency", "sla_minutes"]
    avail = [c for c in order_cols if c in orders.columns]
    df = deliveries.merge(
        orders[avail].drop_duplicates("order_id"),
        on="order_id",
        how="left",
        suffixes=("", "_ord"),
    )

    df = _time_features(df)
    df = _spatial_features(df)
    df = _driver_features(df, drivers)
    df = _package_features(df)

    # Ensure all feature columns exist, fill sensible defaults
    defaults = {
        "package_weight_kg":  2.0,
        "congestion_at_time": 0.40,
        "weather_severity":   0.0,
        "stop_number":        0,
        "speed_factor":       1.0,
        "log_experience":     np.log1p(365),
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    keep = [c for c in FEATURE_COLS if c in df.columns] + [TARGET_COL] + [c for c in ID_COLS if c in df.columns]
    return df[keep].dropna(subset=[TARGET_COL]).reset_index(drop=True)


def run_feature_engineering() -> pd.DataFrame:
    print("  Loading raw data …")
    deliveries = pd.read_csv(DATA_DIR / "deliveries.csv")
    orders     = pd.read_csv(DATA_DIR / "orders.csv")
    drivers    = pd.read_csv(DATA_DIR / "drivers.csv")

    features = build_feature_matrix(deliveries, orders, drivers)

    out = OUTPUT_DIR / "features.csv"
    features.to_csv(out, index=False)

    avail_feats = [c for c in FEATURE_COLS if c in features.columns]
    print(f"  ✓ {len(features):,} samples  ×  {len(avail_feats)} features")
    print(f"  ✓ Target — mean: {features[TARGET_COL].mean():.1f} min  std: {features[TARGET_COL].std():.1f} min")
    print(f"  ✓ Saved → {out}")
    return features


if __name__ == "__main__":
    run_feature_engineering()
