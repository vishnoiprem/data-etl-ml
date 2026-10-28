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

from templating import render_template

TEMPLATES = {
    "source": "gs://{{ var.value.source_bucket }}/{{ ds }}/orders.csv",
    "target": "gs://{{ var.value.target_bucket }}/{{ dag.dag_id }}/{{ ds }}/summary.csv",
    "bigquery": "{{ var.value.bq_dataset }}.{{ var.value.bq_table }}",
    "partition": "{{ ds_nodash }}",
    "previous": "gs://{{ var.value.source_bucket }}/{{ prev_ds }}/orders.csv",
    "window": "[{{ data_interval_start }}, {{ data_interval_end }})",
}

variables = {
    "source_bucket": "demo-source-bucket",
    "target_bucket": "demo-target-bucket",
    "bq_dataset": "analytics",
    "bq_table": "orders_enriched",
}

ctx = build_context(
    dag_id="etl_to_gcs",
    logical_date="2026-01-15",
    variables=variables,
)

for name, template in TEMPLATES.items():
    print(f"{name:<10} {template}")
    print(f"{'':<10} -> {render_template(template, ctx)}")
    print()
