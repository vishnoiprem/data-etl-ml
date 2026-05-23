# 🚚 Synapse Logistics — Route Optimisation & ETA Intelligence

> End-to-end ML system for last-mile logistics: XGBoost ETA prediction · Clarke-Wright VRP · Real-time delivery simulation · FastAPI REST backend · Live HTML dashboard

---

## Results at a Glance

| Metric | Baseline (NN) | ML Pipeline | Delta |
|--------|:------------:|:-----------:|:-----:|
| SLA Compliance | 85.2 % | **97.9 %** | +12.7 pp |
| Route Distance | 1,235.9 km | **444.7 km** | −64 % |
| Avg ETA Error | 16.3 min (naive) | **9.7 min** | −40.6 % |
| ETA Within 10 min | — | **61.9 %** | — |
| Simulation Distance | 980.3 km | **568.9 km** | −42 % |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full ML pipeline (data → features → train → optimise → simulate → evaluate)
python run.py

# 3a. Launch the Streamlit dashboard (original)
python run.py --dashboard

# 3b. Launch the FastAPI backend + live HTML dashboard  ← NEW
python run.py --api
#    → Open http://localhost:8000
#    → API docs: http://localhost:8000/docs
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SYNAPSE LOGISTICS — PIPELINE                     │
└─────────────────────────────────────────────────────────────────────┘

  STEP 1              STEP 2                STEP 3
  ──────────          ──────────────        ────────────────
  Data Gen            Feature Eng           ETA Model
  30 days             15 predictors         XGBoost
  ~300 orders/day ──▶ spatial/temporal ──▶  MAE 9.7 min
  45 drivers          traffic/driver        40.6% vs naive
  3 hubs / 6 zones
       │
       └─────────────────────────────────────────────┐
                                                      ▼
  STEP 4                                    STEP 5
  ──────────────────────────────────        ──────────────────────────────
  Route Optimisation (VRP)                  Delivery Simulation
  NN greedy (baseline)                      baseline: NN + naive ETA
    → Clarke-Wright savings                 ml: CW+2opt+ETA-guided
    → 2-opt local search                    332 orders × 45 drivers
    → ETA-guided reorder         ─────────▶ SLA: 85.2% → 97.9%
  64% distance reduction                    dist: 980 → 569 km
       │
       ▼
  STEP 6                            STEP 7
  ──────────────────                ──────────────────────────────────────
  Evaluation Report                 Dashboard
  KPI report card      ──────────▶  FastAPI  ←──▶  HTML/JS frontend
  zone SLA heatmap                  /api/*           6 tabs + live SSE
  driver performance                :8000            Plotly + Leaflet
```

---

## ML Pipeline — Step by Step

| Step | Module | Description |
|------|--------|-------------|
| 1 | `data/generate_data.py` | Synthetic London-like city: 6 zones, 3 hubs, 45 drivers, 30 days of orders with realistic traffic & weather |
| 2 | `features/feature_engineering.py` | 15-feature matrix: spatial (distance, hub dist), temporal (hour, peak), traffic (congestion), driver (experience, speed), package (weight, urgency) |
| 3 | `models/eta/train.py` | XGBoost regressor; time-based train/test split (last 7 days held out); persists model + feature importance to `artifacts/` |
| 4 | `models/routing/optimizer.py` | NN baseline → Clarke-Wright Savings (VRP) → 2-opt local search → ETA-guided stop reordering |
| 5 | `pipeline/simulator.py` | Event-driven day simulation: walks each driver's route stop-by-stop, applies congestion + weather + noise, records actual vs SLA |
| 6 | `evaluation/metrics.py` | Report card: ETA metrics, routing comparison table, zone SLA heatmap, driver performance |
| 7 | `api/app.py` + `frontend/index.html` | FastAPI REST backend + single-page HTML dashboard with 6 tabs and SSE live feed |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data simulation | NumPy, Pandas |
| ML model | XGBoost (GradientBoosting fallback) |
| Route optimisation | Custom Clarke-Wright + 2-opt |
| Backend API | FastAPI + Uvicorn |
| Frontend | Vanilla JS, Plotly.js, Leaflet.js, Tailwind CSS |
| Streamlit dashboard | Streamlit + Plotly |
| Serialisation | joblib, JSON |

---

## Project Structure

```
9-Logistics-Route-Optimisation/
├── run.py                        ← pipeline runner + launcher
├── requirements.txt
│
├── data/
│   ├── generate_data.py          ← synthetic data generator
│   └── sample/                   ← generated CSV + JSON outputs
│       ├── drivers.csv
│       ├── orders.csv
│       ├── deliveries.csv
│       ├── today_orders.csv
│       ├── today_traffic.csv
│       ├── routes_ml.csv
│       ├── routes_baseline.csv
│       ├── simulation_summary.json
│       └── routing_comparison.csv
│
├── features/
│   └── feature_engineering.py   ← 15-feature matrix builder
│
├── models/
│   ├── eta/
│   │   ├── train.py              ← XGBoost training
│   │   ├── predict.py            ← inference wrapper
│   │   └── artifacts/            ← eta_model.pkl, metrics.json, etc.
│   └── routing/
│       └── optimizer.py          ← NN / CW / 2-opt / ETA algorithms
│
├── pipeline/
│   └── simulator.py              ← delivery day simulation
│
├── evaluation/
│   └── metrics.py                ← KPI report card
│
├── api/
│   └── app.py                    ← FastAPI backend (REST + SSE)
│
├── frontend/
│   └── index.html                ← single-page live dashboard
│
└── viz/
    └── dashboard.py              ← Streamlit dashboard (alternative)
```

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve HTML dashboard |
| GET | `/api/health` | Health check + data readiness |
| GET | `/api/kpis` | Overview KPIs: simulation, ETA model, algorithm comparison |
| GET | `/api/routes/{pipeline}` | Route data with lat/lon (`ml` or `baseline`) |
| GET | `/api/drivers` | Driver performance stats |
| GET | `/api/trends` | 30-day daily aggregates (SLA, time, volume) |
| GET | `/api/eta-analysis` | ETA metrics + predictions sample + feature importance |
| GET | `/api/operations` | Zone SLA + urgency breakdown |
| GET | `/api/live/stream` | **Server-Sent Events** — simulated live delivery stream |
| GET | `/docs` | Interactive Swagger UI |

### Example: KPI response

```json
{
  "simulation": {
    "baseline": { "sla_compliance_pct": 85.2, "total_distance_km": 980.3, ... },
    "ml":       { "sla_compliance_pct": 97.9, "total_distance_km": 568.9, ... },
    "improvement": { "sla_pct_gain": 12.7, "dist_saved_pct": 42.0, ... }
  },
  "eta_model": {
    "test_metrics": { "mae": 9.71, "rmse": 12.91, "within_10min_pct": 61.9, ... }
  }
}
```

### Live stream event

```json
{
  "order_id": "ORD-47291",
  "zone": "EAST",
  "urgency": "express",
  "actual_minutes": 34.2,
  "predicted_minutes": 31.8,
  "eta_error": 2.4,
  "was_on_time": true,
  "driver_id": "DRV017",
  "timestamp": "2026-05-22T09:14:07.123456"
}
```

---

## Dashboard — 6 Tabs

| Tab | Charts | Description |
|-----|--------|-------------|
| 📊 Overview | KPI cards, algorithm bar charts | Baseline vs ML side-by-side; all three routing algorithms |
| 🗺️ Route Map | Leaflet map, route table | Delivery stops per driver with polylines; toggle ML / Baseline |
| 🎯 ETA Model | Scatter, histogram, feature bar | Actual vs predicted; error distribution; top-15 XGBoost features |
| 🚛 Operations | Zone heatmap, urgency bars, driver scatter | SLA by zone / urgency; driver stops vs SLA bubble chart |
| 📈 Trends | Line charts, bar chart | 30-day SLA, delivery time, and order volume history |
| 🔴 Live Feed | SSE ticker, rolling chart | Real-time delivery events streamed via Server-Sent Events |

---

## Configuration

| Variable | Location | Default | Notes |
|----------|----------|---------|-------|
| `RNG_SEED` | `data/generate_data.py` | `42` | Reproducible data generation |
| `n_days` | `run.py` → `step_generate()` | `30` | History window |
| `orders_per_day` | `run.py` → `step_generate()` | `300` | ~85–115% jitter applied |
| `test_days` | `models/eta/train.py` | `7` | Hold-out window for ETA model |
| API port | `api/app.py` | `8000` | `--port` flag for uvicorn |

---

## Requirements

```
Python 3.10+
numpy, pandas, scikit-learn, xgboost
plotly, streamlit          ← Streamlit dashboard
fastapi, uvicorn[standard] ← Live API dashboard
scipy, tqdm, joblib, matplotlib, seaborn
```

Install: `pip install -r requirements.txt`
