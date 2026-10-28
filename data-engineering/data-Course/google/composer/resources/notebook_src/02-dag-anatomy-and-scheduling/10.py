from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print("COURSE_ROOT =", COURSE_ROOT)
print("project/ present:", (COURSE_ROOT / "project").exists())
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())

import local_runner
print("local_runner loaded from:", local_runner.__file__)

from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    render_rejects_csv,
    reject_counts,
    logical_date_window,
    partition_for_date,
)

from local_runner import DAG, Task


def read_orders(run, context):
    """Read the raw CSV."""
    path = COURSE_ROOT / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


def transform(run, context):
    """Validate and transform."""
    raw = run.pull("read_orders") or []
    accepted, rejected = transform_orders(raw)
    run.xcom.push("transform", "accepted", accepted)
    run.xcom.push("transform", "rejected", rejected)
    return {"accepted": len(accepted), "rejected": len(rejected)}


def aggregate(run, context):
    """Summarise by region."""
    accepted = run.pull("transform", "accepted") or []
    summary = summarise_by_region(accepted)
    run.xcom.push("aggregate", "summary", summary)
    return summary


def write_summary(run, context):
    """Write the summary, tagged with the run's logical date."""
    summary = run.pull("aggregate", "summary") or {}
    window = logical_date_window(run.logical_date)
    out = COURSE_ROOT / "out" / "notebook02" / run.logical_date / "summary.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_summary_csv(summary), encoding="utf-8")
    return {
        "path": str(out),
        "window": window,
        "rows": render_summary_csv(summary),
    }


demo = DAG(
    "scheduling_demo",
    tasks=[
        Task("read_orders", read_orders, dependencies=[]),
        Task("transform", transform, dependencies=["read_orders"]),
        Task("aggregate", aggregate, dependencies=["transform"]),
        Task("write_summary", write_summary, dependencies=["aggregate"]),
    ],
    schedule="@daily",
    start_date="2026-01-15",
    catchup=False,
    max_active_runs=1,
    description="Demonstrates logical date, data interval and execution order.",
)

print(demo.describe())
