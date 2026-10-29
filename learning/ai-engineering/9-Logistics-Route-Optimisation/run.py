#!/usr/bin/env python3
"""
Logistics Route Optimisation — End-to-End Pipeline Runner

Usage:
  python run.py                   # run all steps then launch dashboard
  python run.py --steps generate  # only generate data
  python run.py --steps train     # only train ETA model
  python run.py --steps all       # all steps, then ask about dashboard
  python run.py --no-dashboard    # run all steps, skip dashboard launch
  python run.py --dashboard       # skip pipeline, launch dashboard only

Pipeline steps:
  1. Generate synthetic data    (30 days, ~300 orders/day)
  2. Feature engineering        (15-feature matrix)
  3. Train ETA model            (XGBoost, time-based split)
  4. Route optimisation         (NN vs CW+2opt vs ETA-guided)
  5. Delivery simulation        (baseline vs ML pipeline)
  6. Evaluation report          (KPI report card)
  7. Streamlit dashboard        (interactive UI)
"""

import argparse
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

DIVIDER = "─" * 66


def _header(step: int, title: str):
    print(f"\n{'═' * 66}")
    print(f"  STEP {step}  │  {title}")
    print(f"{'═' * 66}")


def step_generate():
    _header(1, "Generate Synthetic Logistics Data")
    from data.generate_data import generate_all_data
    generate_all_data(n_days=30, orders_per_day=300)


def step_features():
    _header(2, "Feature Engineering  (15 predictors)")
    from features.feature_engineering import run_feature_engineering
    run_feature_engineering()


def step_train():
    _header(3, "Train ETA Prediction Model  (XGBoost)")
    from models.eta.train import train_eta_model
    train_eta_model()


def step_optimise():
    _header(4, "Route Optimisation Benchmark")
    import pandas as pd
    from models.routing.optimizer import RoutingOptimizer

    DATA = _ROOT / "data" / "sample"
    orders  = pd.read_csv(DATA / "today_orders.csv")
    drivers = pd.read_csv(DATA / "drivers.csv")
    traffic = pd.read_csv(DATA / "today_traffic.csv")

    try:
        from models.eta.predict import predict_eta
        eta_fn = predict_eta
    except Exception:
        eta_fn = None

    opt = RoutingOptimizer(eta_model_fn=eta_fn)
    print(f"\n  Running 3 algorithms on {len(orders)} orders, {len(drivers)} drivers …\n")
    comparison = opt.compare_algorithms(orders, drivers, traffic, current_hour=9)

    # Pretty print comparison table
    print(f"  {'Algorithm':<35} {'Dist (km)':>10} {'Time (h)':>10} {'Saved %':>9} {'Runtime':>9}")
    print(f"  {DIVIDER}")
    baseline_dist = comparison["Total Distance (km)"].iloc[0]
    for _, row in comparison.iterrows():
        saved = row["Distance Saved (%)"]
        bar   = "▓" * int(abs(saved) / 2) if saved != 0 else ""
        print(
            f"  {row['Algorithm']:<35} {row['Total Distance (km)']:>10.1f} "
            f"{row['Total Time (h)']:>10.2f} {saved:>8.1f}% {row['Runtime (s)']:>8.3f}s"
        )

    comparison.to_csv(DATA / "routing_comparison.csv", index=False)
    print(f"\n  ✓ Saved → data/sample/routing_comparison.csv")


def step_simulate():
    _header(5, "Delivery Day Simulation  (Baseline vs ML)")
    from pipeline.simulator import run_simulation
    run_simulation(verbose=True)


def step_evaluate():
    _header(6, "Performance Report Card")
    from evaluation.metrics import print_report_card
    print_report_card()


def step_dashboard():
    _header(7, "Launching Streamlit Dashboard")
    dashboard = _ROOT / "viz" / "dashboard.py"
    print(f"\n  Command: streamlit run {dashboard}\n")
    os.execv(
        sys.executable,
        [sys.executable, "-m", "streamlit", "run", str(dashboard), "--server.headless", "false"],
    )


def step_api():
    _header(7, "Launching Live Dashboard  (FastAPI + HTML Frontend)")
    print(f"\n  Dashboard : http://localhost:8000")
    print(f"  API docs  : http://localhost:8000/docs\n")
    os.execv(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "api.app:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
    )


# ── CLI ────────────────────────────────────────────────────────────────────────

STEP_MAP = {
    "generate":  step_generate,
    "features":  step_features,
    "train":     step_train,
    "optimise":  step_optimise,
    "simulate":  step_simulate,
    "evaluate":  step_evaluate,
    "dashboard": step_dashboard,
    "api":       step_api,
}

ALL_STEPS = ["generate", "features", "train", "optimise", "simulate", "evaluate"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--steps", nargs="+", default=["all"],
        choices=list(STEP_MAP.keys()) + ["all"],
        help="Steps to run (default: all)",
    )
    parser.add_argument("--no-dashboard", action="store_true", help="Skip dashboard launch")
    parser.add_argument("--dashboard",    action="store_true", help="Launch Streamlit dashboard only")
    parser.add_argument("--api",          action="store_true", help="Launch FastAPI + HTML live dashboard")
    args = parser.parse_args()

    print(f"\n{'╔' + '═'*64 + '╗'}")
    print(f"{'║':1}{'  🚚  LOGISTICS ROUTE OPTIMISATION — END-TO-END PIPELINE':^64}{'║':1}")
    print(f"{'╚' + '═'*64 + '╝'}")

    if args.dashboard:
        step_dashboard()
        return

    if args.api:
        step_api()
        return

    steps = ALL_STEPS if "all" in args.steps else args.steps

    t_total = time.time()
    for name in steps:
        if name in STEP_MAP:
            STEP_MAP[name]()

    elapsed = time.time() - t_total
    print(f"\n{'═' * 66}")
    print(f"  ✅  Pipeline complete in {elapsed:.1f}s")
    print(f"{'═' * 66}\n")

    if not args.no_dashboard and "all" in args.steps or args.steps == ALL_STEPS:
        print("  Launching Streamlit dashboard …  (Ctrl+C to exit)")
        time.sleep(1)
        step_dashboard()


if __name__ == "__main__":
    main()
