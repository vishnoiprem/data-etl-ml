#!/usr/bin/env python3
"""scripts/ablation_table.py — emit the README's "Real numbers" table from MLflow.

Reads the last N runs in the configured experiment, pulls the evaluation
metrics + cost columns, and emits a markdown table to `AB_RESULTS.md`.
The README references this script so the table is never hand-edited.

Usage:
    python scripts/ablation_table.py            # writes AB_RESULTS.md
    python scripts/ablation_table.py --print    # prints to stdout
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def _try_mlflow():
    try:
        import mlflow  # type: ignore
        from mlflow.tracking import MlflowClient  # type: ignore
        return mlflow, MlflowClient
    except ImportError:
        return None, None


def build_table(runs: list[Any]) -> str:
    """Render a markdown table from a list of MLflow run summaries."""
    if not runs:
        return "_no runs yet — run `make train` first._\n"

    headers = [
        "Run ID",
        "Started",
        "lora_r",
        "lr",
        "arc",
        "hellaswag",
        "truthfulqa",
        "held_out",
        "train_cost_usd",
        "final_loss",
    ]
    rows = ["| " + " | ".join(headers) + " |",
            "|" + "|".join(["---"] * len(headers)) + "|"]

    for r in runs:
        p = r.data.params
        m = r.data.metrics
        rows.append("| " + " | ".join([
            (r.info.run_id[:8] or "-"),
            _fmt_dt(r.info.start_time),
            _fmt(p.get("TrainConfig.lora_r"), "16"),
            _fmt(p.get("TrainConfig.lr"), "2e-4"),
            _fmt(m.get("eval_arc_challenge_acc")),
            _fmt(m.get("eval_hellaswag_acc")),
            _fmt(m.get("eval_truthfulqa_mc2_acc")),
            _fmt(m.get("eval_held_out_score")),
            _fmt(m.get("train_cost_usd"), prec=2),
            _fmt(m.get("final_train_loss"), prec=3),
        ]) + " |")
    return "\n".join(rows) + "\n"


def _fmt(v: Any, default: str = "-", prec: int = 3) -> str:
    if v is None:
        return default
    try:
        f = float(v)
        if 0 <= f <= 1 and prec == 3 and f != 0:
            return f"{f:.3f}"
        return f"{f:.{prec}f}"
    except (ValueError, TypeError):
        return str(v)


def _fmt_dt(ms: int | None) -> str:
    if not ms:
        return "-"
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print", action="store_true", help="Print to stdout instead of writing AB_RESULTS.md.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    mlflow, MlflowClient = _try_mlflow()
    if mlflow is None:
        print("mlflow not installed — install requirements first", file=sys.stderr)
        return 1

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment = os.environ.get("MLFLOW_EXPERIMENT_NAME", "mlops-finetune-genai")

    try:
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient(tracking_uri=tracking_uri)
        exp = client.get_experiment_by_name(experiment)
        if exp is None:
            print(f"# Experiment `{experiment}` not found at {tracking_uri}", file=sys.stderr)
            return 1
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            max_results=args.limit,
            order_by=["start_time DESC"],
        )
    except Exception as e:
        print(f"# Could not reach MLflow at {tracking_uri}: {e}", file=sys.stderr)
        return 1

    table = "# Auto-generated from MLflow\n\n" + build_table(list(runs))

    if args.print:
        print(table)
    else:
        out = REPO_ROOT / "AB_RESULTS.md"
        out.write_text(table)
        print(f"wrote {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
