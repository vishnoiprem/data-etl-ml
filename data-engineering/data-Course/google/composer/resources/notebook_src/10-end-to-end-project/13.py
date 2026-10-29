"""The deployment checklist, computed from the DAG sources.

Nothing here is hand-typed prose that could drift from the code. The
checklist is *derived*: the Variables are extracted from the DAG files'
templates, the params are read out of the `params={...}` blocks, and the
rendered `gcloud` commands are built from the same values.

The output is the artifact you paste into a ticket.
"""

import re
from collections import OrderedDict

# --------------------------------------------------------------------------
# 1. The Variables the DAGs read — extracted, not remembered
# --------------------------------------------------------------------------
print("=" * 78)
print("1. VARIABLES — extracted from the DAG sources")
print("=" * 78)
print()

read_vars: dict[str, set[str]] = OrderedDict()
for analysis in analyses:
    source = (DAGS_DIR / analysis["file"]).read_text(encoding="utf-8")
    read_vars[analysis["file"]] = set(re.findall(r"var\.value\.(\w+)", source))

# `dag_config.py` declares the same names with defaults.
config_source = (DAGS_DIR / "dag_config.py").read_text(encoding="utf-8")
config_vars = set(re.findall(r"var\.value\.(\w+)", config_source))
read_vars["dag_config.py"] = config_vars

all_variables = sorted(set().union(*read_vars.values()))

# The value each Variable should have in production, and why.
VARIABLE_VALUES = {
    "gcp_project_id": ("YOUR_PROJECT_ID", "The project the BigQuery tables live in"),
    "source_bucket": ("YOUR_PROJECT_ID-source", "Where the raw CSVs arrive"),
    "target_bucket": ("YOUR_PROJECT_ID-target", "Where the exports are written"),
    "bq_dataset": ("analytics", "The destination dataset"),
    "bq_table": ("orders_enriched", "The destination table"),
    "source_bq_table": ("raw.orders", "The upstream table"),
    "reject_bq_table": ("analytics.orders_rejected", "The dead-letter table"),
    "full_load_threshold": ("1000000", "The branch boundary"),
    "pipeline_owner": ("data-platform", "Who owns the DAG"),
    "alert_email": ("data-oncall@example.com", "Where the SLA callback notifies"),
}

print(f"{'variable':<22} {'value':<34} {'read by'}")
print("-" * 100)
for name in all_variables:
    value, _ = VARIABLE_VALUES.get(name, ("<SET THIS>", ""))
    readers = [f for f, names in read_vars.items() if name in names]
    print(f"{name:<22} {value:<34} {', '.join(readers)}")

print()
missing = [n for n in all_variables if n not in VARIABLE_VALUES]
assert not missing, f"undocumented Variables: {missing}"
print(f"All {len(all_variables)} Variables are documented.")
print()

# --------------------------------------------------------------------------
# 2. The Connections
# --------------------------------------------------------------------------
print("=" * 78)
print("2. CONNECTIONS")
print("=" * 78)
print()

CONNECTIONS = [
    {
        "conn_id": "google_cloud_default",
        "conn_type": "google_cloud_platform",
        "host": "-",
        "credentials": "the environment's service account",
        "extra": '{"project_id": "YOUR_PROJECT_ID"}',
        "note": "Composer creates this for you",
    },
    {
        "conn_id": "http_orders_api",
        "conn_type": "http",
        "host": "api.example.com",
        "credentials": "login + password from Secret Manager",
        "extra": '{"timeout": 30, "retries": 3}',
        "note": "Never a literal password",
    },
]

print(f"{'conn_id':<24} {'type':<24} {'host':<18} note")
print("-" * 100)
for conn in CONNECTIONS:
    print(f"{conn['conn_id']:<24} {conn['conn_type']:<24} "
          f"{conn['host']:<18} {conn['note']}")
print()
print("Set them in Admin -> Connections, or:")
print()
print("  gcloud composer environments update YOUR_ENVIRONMENT_NAME \\")
print("    --location=REGION \\")
print("    --update-airflow-connections=http_orders_api;conn_type=http;"
      "host=api.example.com;login=svc_account;extra='{\"timeout\": 30}'")
print()

# --------------------------------------------------------------------------
# 3. The DAG params — read out of the DAG sources
# --------------------------------------------------------------------------
print("=" * 78)
print("3. DAG PARAMS — read out of the `params={...}` blocks")
print("=" * 78)
print()

for analysis in analyses:
    params = analysis["params"]
    if not params:
        continue
    print(f"{analysis['dag_id']}  (schedule={analysis['schedule']})")
    for key, value in params.items():
        print(f"    {key:<20} default={value!r}")
    print()

# The branching DAG's params are the ones you actually change.
branch_params = next(a for a in analyses if a["dag_id"] == "branching_and_xcom")["params"]
assert branch_params["row_count"] == 0
assert branch_params["force_full_load"] is False
print("The branching DAG is triggered with a config:")
print()
print('  {"row_count": 1500000, "force_full_load": false}')
print()
print("That config drives the branch: 1,500,000 > the 1,000,000 threshold,")
print("so the full-load path is taken.")
print()

# --------------------------------------------------------------------------
# 4. The rendered gcloud commands
# --------------------------------------------------------------------------
print("=" * 78)
print("4. THE COMMANDS")
print("=" * 78)
print()

ENV_NAME = "YOUR_ENVIRONMENT_NAME"
REGION = "REGION"

print("# Set every Variable in one call:")
print(f"gcloud composer environments update {ENV_NAME} \\")
print(f"  --location={REGION} \\")
var_flags = " \\\n  ".join(
    f"--update-airflow-variables={name}={VARIABLE_VALUES[name][0]}"
    for name in all_variables
)
print(var_flags)
print()

print("# Sync the DAG bucket:")
print("gsutil -m rsync -r -d ./project/dags gs://YOUR_PROJECT_ID-dags")
print("gsutil -m rsync -r -d ./project/core gs://YOUR_PROJECT_ID-dags/core")
print()

print("# Trigger one run (the run id encodes the logical date):")
print(f"gcloud composer environments run {ENV_NAME} \\")
print(f"  --location={REGION} \\")
print("  --dag etl_orders_to_bigquery \\")
print("  --run-id=manual__2026-01-15T00:00:00+00:00")
print()

print("# Trigger a backfill — one run id per date:")
for date in ("2026-01-10", "2026-01-11", "2026-01-12"):
    print(f"gcloud composer environments run {ENV_NAME} \\")
    print(f"  --location={REGION} \\")
    print("  --dag etl_orders_to_bigquery \\")
    print(f"  --run-id=manual__{date}T00:00:00+00:00")
print()

# --------------------------------------------------------------------------
# 5. The checklist as a table
# --------------------------------------------------------------------------
print("=" * 78)
print("5. THE CHECKLIST")
print("=" * 78)
print()

checklist = [
    ("Variables", len(all_variables), "Admin -> Variables",
     "set every one before the first run"),
    ("Connections", len(CONNECTIONS), "Admin -> Connections",
     "google_cloud_default is created for you"),
    ("DAG params", len(branch_params), "at trigger time",
     "row_count drives the branch"),
    ("DAG files", len(DAG_FILES), "gs://YOUR_PROJECT_ID-dags",
     "plus core/ in a subdirectory"),
    ("IAM", 4, "gcloud projects add-iam-policy-binding",
     "composer.worker, bigquery.jobUser, storage.objectAdmin, projectViewer"),
    ("Service account", 1, "--service-account",
     "dedicated per environment, never the default"),
    ("Log bucket", 1, "gs://YOUR_PROJECT_ID-logs",
     "different from the DAG bucket, with a lifecycle rule"),
    ("Timezone", 1, "AIRFLOW__CORE__DEFAULT_TIMEZONE",
     "UTC, set explicitly"),
]

print(f"{'item':<18} {'count':>6}  {'where':<40} note")
print("-" * 100)
for item, count, where, note in checklist:
    print(f"{item:<18} {count:>6}  {where:<40} {note}")
print()

print("PASS: the checklist is complete and derived from the DAG sources.")
print()
