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

from templating import build_context, render_template

DEV_VARS = {
    "gcp_project_id": "demo-project",
    "source_bucket": "demo-source-bucket",
    "target_bucket": "demo-target-bucket",
    "bq_dataset": "analytics",
    "bq_table": "orders_enriched",
}

PROD_VARS = {
    "gcp_project_id": "acme-data-prod",
    "source_bucket": "acme-prod-raw",
    "target_bucket": "acme-prod-curated",
    "bq_dataset": "analytics_prod",
    "bq_table": "orders_enriched",
}

FIELDS = ("GCP_PROJECT_ID", "SOURCE_BUCKET", "TARGET_BUCKET", "BQ_DATASET", "BQ_TABLE")

import dag_config

for label, variables in (("DEV", DEV_VARS), ("PROD", PROD_VARS)):
    ctx = build_context(
        dag_id="etl_to_gcs",
        logical_date="2026-01-15",
        variables=variables,
    )
    print(f"--- {label} ---")
    for field in FIELDS:
        rendered = render_template(getattr(dag_config, field), ctx)
        print(f"  {field:<16} {rendered}")
    print()
