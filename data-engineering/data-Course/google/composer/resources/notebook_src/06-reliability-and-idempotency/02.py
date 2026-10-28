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

from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    partition_for_date,
    dedup_key,
    filter_rows_for_partition,
)
from idempotent_load import apply_load
from dedup_load import dedup_rows

SAMPLE_DIR = COURSE_ROOT / "sample_data"
lines = (SAMPLE_DIR / "orders.csv").read_text(encoding="utf-8").splitlines()

accepted, rejected = transform_orders(lines)
print(f"accepted={len(accepted)} rejected={len(rejected)}")

summary = summarise_by_region(accepted)
print()
print(render_summary_csv(summary))
