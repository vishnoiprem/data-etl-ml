"""
Synapse Logistics — FastAPI Backend

Serves the live HTML dashboard and exposes REST + SSE endpoints.

Run:
    python run.py --api
  or directly:
    uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

DATA_DIR      = _ROOT / "data" / "sample"
ARTIFACTS_DIR = _ROOT / "models" / "eta" / "artifacts"
FRONTEND_DIR  = _ROOT / "frontend"

app = FastAPI(
    title="Synapse Logistics API",
    description="Route Optimisation & ETA Intelligence — REST + SSE",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _data_ready() -> bool:
    return (DATA_DIR / "simulation_summary.json").exists()


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "data_ready": _data_ready(),
        "files": {
            "routes_ml": (DATA_DIR / "routes_ml.csv").exists(),
            "eta_model": (ARTIFACTS_DIR / "eta_model.pkl").exists(),
            "simulation": (DATA_DIR / "simulation_summary.json").exists(),
        },
    }


# ── Overview KPIs ──────────────────────────────────────────────────────────────

@app.get("/api/kpis", tags=["data"])
def get_kpis() -> dict:
    sim = _json(DATA_DIR / "simulation_summary.json")
    eta = _json(ARTIFACTS_DIR / "metrics.json")
    rc  = _csv(DATA_DIR / "routing_comparison.csv")
    return {
        "simulation": sim,
        "eta_model":  eta,
        "routing_comparison": rc.to_dict(orient="records") if not rc.empty else [],
        "timestamp": datetime.now().isoformat(),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/api/routes/{pipeline}", tags=["data"])
def get_routes(pipeline: str) -> list[dict]:
    if pipeline not in ("ml", "baseline"):
        raise HTTPException(400, "pipeline must be 'ml' or 'baseline'")

    df      = _csv(DATA_DIR / f"routes_{pipeline}.csv")
    orders  = _csv(DATA_DIR / "today_orders.csv")

    if df.empty:
        return []

    if not orders.empty and "dropoff_lat" in orders.columns:
        df = df.merge(
            orders[["order_id", "dropoff_lat", "dropoff_lon"]],
            on="order_id", how="left",
        )

    keep = [c for c in [
        "order_id", "driver_id", "hub_id", "stop_number", "zone",
        "urgency", "sla_minutes", "distance_km", "actual_minutes",
        "was_on_time", "predicted_minutes", "eta_error_minutes",
        "dropoff_lat", "dropoff_lon",
    ] if c in df.columns]

    return df[keep].fillna(0).to_dict(orient="records")


# ── Drivers ────────────────────────────────────────────────────────────────────

@app.get("/api/drivers", tags=["data"])
def get_drivers() -> list[dict]:
    routes  = _csv(DATA_DIR / "routes_ml.csv")
    drivers = _csv(DATA_DIR / "drivers.csv")

    if routes.empty:
        return []

    stats = (
        routes.groupby("driver_id")
        .agg(
            stops     = ("order_id", "count"),
            sla_pct   = ("was_on_time", lambda x: round(x.mean() * 100, 1)),
            avg_time  = ("actual_minutes", lambda x: round(x.mean(), 1)),
            total_dist= ("distance_km",    lambda x: round(x.sum(),  1)),
        )
        .reset_index()
        .sort_values("sla_pct", ascending=False)
    )

    if not drivers.empty and "driver_id" in drivers.columns:
        stats = stats.merge(
            drivers[["driver_id", "experience_days", "home_hub_id"]],
            on="driver_id", how="left",
        )

    return stats.fillna(0).to_dict(orient="records")


# ── Trends ─────────────────────────────────────────────────────────────────────

@app.get("/api/trends", tags=["data"])
def get_trends() -> list[dict]:
    deliveries = _csv(DATA_DIR / "deliveries.csv")
    if deliveries.empty:
        return []

    deliveries["date"] = pd.to_datetime(deliveries["date"]).dt.strftime("%Y-%m-%d")
    count_col = "delivery_id" if "delivery_id" in deliveries.columns else "order_id"

    daily = (
        deliveries.groupby("date")
        .agg(
            orders      = (count_col,        "count"),
            sla_pct     = ("was_on_time",     lambda x: round(x.mean() * 100, 1)),
            avg_time_min= ("actual_minutes",  lambda x: round(x.mean(), 1)),
            avg_dist_km = ("distance_km",     lambda x: round(x.mean(), 2)),
        )
        .reset_index()
    )

    if "dropoff_zone" in deliveries.columns:
        zone_dow = (
            deliveries.assign(dow=pd.to_datetime(deliveries["date"]).dt.day_name())
            .groupby(["dropoff_zone", "dow"])["was_on_time"]
            .mean()
            .mul(100)
            .round(1)
            .reset_index()
            .rename(columns={"was_on_time": "sla_pct"})
        )
        return {
            "daily":    daily.to_dict(orient="records"),
            "zone_dow": zone_dow.to_dict(orient="records"),
        }

    return {"daily": daily.to_dict(orient="records"), "zone_dow": []}


# ── ETA Analysis ───────────────────────────────────────────────────────────────

@app.get("/api/eta-analysis", tags=["data"])
def get_eta() -> dict:
    metrics = _json(ARTIFACTS_DIR / "metrics.json")
    preds   = _csv(ARTIFACTS_DIR / "test_predictions.csv")
    fi      = _csv(ARTIFACTS_DIR / "feature_importance.csv")

    if preds.empty:
        return {"metrics": metrics, "predictions_sample": [], "feature_importance": []}

    sample = preds.sample(min(2000, len(preds)), random_state=1)
    sample["error"] = (sample["predicted_minutes"] - sample["actual_minutes"]).round(1)

    return {
        "metrics": metrics,
        "predictions_sample": sample[["actual_minutes", "predicted_minutes", "error"]].to_dict(orient="records"),
        "feature_importance": fi.head(15).to_dict(orient="records") if not fi.empty else [],
    }


# ── Operations ─────────────────────────────────────────────────────────────────

@app.get("/api/operations", tags=["data"])
def get_operations() -> dict:
    ml_df = _csv(DATA_DIR / "routes_ml.csv")
    if ml_df.empty:
        return {"zone_sla": [], "urgency_sla": []}

    zone_sla = (
        ml_df.groupby("zone")
        .agg(
            orders  = ("order_id", "count"),
            sla_pct = ("was_on_time", lambda x: round(x.mean() * 100, 1)),
        )
        .reset_index()
        .sort_values("sla_pct")
        .to_dict(orient="records")
    )

    urgency_sla = (
        ml_df.groupby("urgency")
        .agg(
            orders  = ("order_id", "count"),
            sla_pct = ("was_on_time", lambda x: round(x.mean() * 100, 1)),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    return {"zone_sla": zone_sla, "urgency_sla": urgency_sla}


# ── Live SSE stream ────────────────────────────────────────────────────────────

_ZONES     = ["CENTRAL", "EAST", "WEST", "NORTH", "SOUTH", "CITY"]
_URGENCIES = [("same_day", 60, 22, 9), ("express", 120, 38, 12), ("standard", 300, 52, 15)]


@app.get("/api/live/stream", tags=["live"])
async def live_stream() -> StreamingResponse:
    """Server-Sent Events stream of simulated live delivery completions."""

    async def generate():
        yield "retry: 3000\n\n"
        while True:
            urg, sla, mu, sigma = random.choice(_URGENCIES)
            actual    = round(max(random.gauss(mu, sigma), 3.0), 1)
            predicted = round(max(actual + random.gauss(0, 5), 1.0), 1)
            on_time   = actual <= sla

            event: dict[str, Any] = {
                "order_id":          f"ORD-{random.randint(10_000, 99_999)}",
                "zone":              random.choice(_ZONES),
                "urgency":           urg,
                "actual_minutes":    actual,
                "predicted_minutes": predicted,
                "eta_error":         round(abs(actual - predicted), 1),
                "was_on_time":       on_time,
                "driver_id":         f"DRV{random.randint(1, 45):03d}",
                "timestamp":         datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(random.uniform(1.2, 3.0))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Frontend ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend() -> HTMLResponse:
    html = FRONTEND_DIR / "index.html"
    if not html.exists():
        return HTMLResponse("<h1>Frontend not found — run <code>python run.py --api</code></h1>")
    return HTMLResponse(content=html.read_text())


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
