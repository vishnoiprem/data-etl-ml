# 22 — Build a Visual ETL Pipeline with Glue Studio

A runnable, **offline-first** mirror of the AWS Skill Builder lab
**"Build a Visual ETL Pipeline with Glue Studio."** Seven stages, seven
shell scripts that map exactly to the lab's "click in the console"
instructions, plus a pytest suite that drives the same in-process Glue
Studio shim. No AWS credentials needed for verification.

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ graph/customer_etl_graph.json                                         │
  │                                                                       │
  │  [DataCatalogSource] ──► [Filter status='active'] ──► [Change Schema] │
  │   customers_raw            active_customers            mapped_…      │
  │                                                    (drop status,      │
  │                                                     cast created_at)  │
  │                                                                       │
  │                                                      ──► [S3 Parquet]  │
  │                                                           curated_…    │
  └──────────────────────────────────────────────────────────────────────┘

  Glue Studio turns the graph above into a PySpark script. The lab's
  centerpiece is reading that auto-generated script (the "Job Script"
  tab); offline we ship the SAME script in `glue_jobs/` and run it
  against a 100-line `awsglue/` shim that mirrors the AWS package.

                       ┌──────────────────────────────────┐
                       │   glue_jobs/customer_etl_…py      │
                       │                                     │
                       │   from awsglue.transforms import *  │
                       │   from awsglue.context  import GlueContext
                       │   from awsglue.job       import Job │
                       │                                     │
                       │   glueContext.create_dynamic_frame │
                       │     .from_catalog(...)               │
                       │   Filter.apply(...)                  │
                       │   ApplyMapping.apply(...)            │
                       │   write_dynamic_frame                │
                       │     .from_options(format="glueparquet") │
                       └───────────────┬────────────────────┘
                                       │
                                       ▼  (production: real awsglue)
                                            (offline: awsglue/ shim)
                       ┌──────────────────────────────────┐
                       │   Glue-managed Spark (or local)    │
                       │                                     │
                       │   parquet/curated_customers/        │
                       │     part-00000-…snappy.parquet      │
                       └───────────────┬────────────────────┘
                                       │
                                       ▼
                       ┌──────────────────────────────────┐
                       │   Athena (engine v3)               │
                       │     SELECT … FROM curated_customers│
                       └────────────────────────────────────┘
```

## Files

| Path                                                       | Purpose                                  |
|------------------------------------------------------------|------------------------------------------|
| `graph/customer_etl_graph.json`                            | The 4-node visual graph as data          |
| `glue_jobs/customer_etl_glue_studio.py`                    | Auto-generated PySpark (the "Job Script" tab) |
| `awsglue/`                                                 | Local shim mirroring the `awsglue` package |
| `awsglue/_catalog/studio_db_local/customers_raw/`          | Offline Glue Data Catalog (CSV + schema)  |
| `sample_data/customers_raw.csv`                            | 12-row seed CSV (9 active, 3 inactive)    |
| `01_build_visual_etl_pipeline_with_glue_studio.py`         | Self-asserting driver (7 stages, 49 checks) |
| `scripts/00_set_lab.sh`                                    | Helper: set BUCKET / DATABASE / ROLE_ARN  |
| `scripts/01_inspect_catalog.sh` through `06_teardown.sh`   | Six stage scripts                         |
| `scripts/run_all.sh`                                       | Optional: run stages 1–5 in sequence      |
| `tests/conftest.py`                                        | Pytest fixtures: SparkSession + tmpdir    |
| `tests/test_visual_job.py`                                 | 13 pytest tests, no AWS creds             |
| `README.md`                                                | This file                                |

## The 7 lab stages — mapped to artifacts

| Stage | Lab step                                                       | Artifact                                |
|-------|----------------------------------------------------------------|-----------------------------------------|
| 1     | Inspect the pre-crawled `customers_raw` Glue catalog table      | `01_inspect_catalog.sh`, `test_stage1_*` |
| 2     | Author the 4-node visual graph in Glue Studio                  | `graph/customer_etl_graph.json`         |
| 3     | Glue Studio emits PySpark (the "Job Script" tab)               | `glue_jobs/customer_etl_glue_studio.py` |
| 4     | Run the job, wait for SUCCEEDED                                | `02_create_visual_job.sh` + `03_run_visual_job.sh`, `test_stage4_*` |
| 5     | Inspect Parquet: 9 rows, status dropped, created_at=timestamp  | driver stage 5, `test_stage5_*`        |
| 6     | Re-read the auto-generated script (your PySpark knowledge)     | driver stage 6                          |
| 7     | Athena queries (count / top-3 / per-day)                       | `05_query_curated.sh`, `test_stage7_*`  |

## Run it offline (no AWS account)

```bash
cd medium/meta/datavidhya/22_Build_Visual_ETL_Pipeline_With_Glue_Studio/

# Self-asserting driver -- 49 checks, all PASS.
../../../.env/bin/python 01_build_visual_etl_pipeline_with_glue_studio.py

# pytest -- 13 tests, all PASS.
../../../.env/bin/python -m pytest tests/ -v
```

The driver and tests run the **same** `glue_jobs/customer_etl_glue_studio.py`
script that production Glue Studio would emit. The only thing that
differs is `awsglue`: production uses the real AWS package; offline
the lab's `awsglue/` directory shadows it because the lab dir is on
`PYTHONPATH`. The script is byte-identical in both environments.

## Run it against a real AWS account

```bash
export BUCKET=glue-studio-visual-etl-bucket-a1b2c3
export DATABASE=studio_db_a1b2c3
export ROLE_ARN="arn:aws:iam::123456789012:role/GlueStudioLabRole-Ab3xYz"
export WORKGROUP=studio-visual-etl-wg-a1b2c3
export AWS_REGION=us-east-1

./scripts/run_all.sh      # stages 1-5
./scripts/06_teardown.sh  # explicit teardown
```

`run_all.sh` runs the five mutating scripts in order. Stage 0 (capture
resource names) is run separately because it requires pasting from the
lab console. Stage 6 (teardown) is also separate so you can inspect the
output before destroying it.

## What each lab stage actually does

### Stage 1 — Inspect the pre-crawled catalog

The lab provisions a Glue Data Catalog table `customers_raw` inside
`studio_db_xxx`. Because Glue Studio's crawler auto-typed every column
as `string` (raw CSV is untyped), the lab has you peek at the schema
to set up the **Change Schema** node downstream.

### Stage 2 — Draw the 4-node graph

In Glue Studio's UI the user drags four nodes onto the canvas:

1. **Data Catalog source** — `studio_db_xxx.customers_raw`
2. **Filter** — predicate `status = 'active'`
3. **Change Schema** — drop `status`, cast `created_at` from string → timestamp
4. **S3 Parquet target** — `s3://$BUCKET/curated/customers/`, register as `curated_customers`

We model this as a JSON graph in `graph/customer_etl_graph.json`. The
driver validates the topology is a linear chain (4 nodes, 3 edges).

### Stage 3 — Glue Studio emits PySpark

The "Job Script" tab shows the PySpark Glue Studio generated. The
script uses `glueContext.create_dynamic_frame.from_catalog`,
`Filter.apply`, `ApplyMapping.apply`, and
`glueContext.write_dynamic_frame.from_options(... format="glueparquet" ...)`.
The driver asserts the script contains each of these calls.

### Stage 4 — Run the job

`02_create_visual_job.sh` registers the job with
`--command "Name=gluestudio,JobMode=VISUAL"`. The actual graph lives
in the lab console (Glue Studio doesn't expose the graph via the API
in a way you can replay from a shell script). `03_run_visual_job.sh`
polls `aws glue get-job-run` every 15s until the run flips to
`SUCCEEDED`.

### Stage 5 — Inspect the Parquet output

9 active customers (12 source rows – 3 inactive). The `status` column
is absent (ApplyMapping dropped it because it wasn't listed in the
mappings). `created_at` is `timestamp`, not `string`.

### Stage 6 — Re-read the auto-generated script

This is the lab's most surprising step: Glue Studio generates Python
that no human would write by hand. The driver asserts the script
contains every API the lab promises (`Filter.apply`, `ApplyMapping.apply`,
`glueContext.write_dynamic_frame.from_options(... format="glueparquet" ...)`).

### Stage 7 — Athena queries

```sql
SELECT COUNT(*) FROM curated_customers;                       -- 9
SELECT name FROM curated_customers
ORDER BY created_at DESC LIMIT 3;                             -- Leo, Kim, Ivan
SELECT DATE(created_at) AS day, COUNT(*)
FROM curated_customers GROUP BY DATE(created_at) ORDER BY day;
-- seven 1s + one 2 (C011 + C012 both joined on 2026-09-27)
```

## Traps the lab expects you to hit

- **Forgetting to list a column in ApplyMapping = silently dropped.**
  Glue Studio's ApplyMapping node has no separate "Drop Fields" node
  -- the absence from the mappings list IS the drop. List every column
  you want to keep. The driver asserts `status` is absent because the
  mappings omit it on purpose.
- **Editing the auto-generated script.** Glue Studio will overwrite
  your changes the next time you click "Save" in the visual editor.
  The script is read-only.
- **Treating `glueparquet` as a different format from `parquet`.** It's
  Parquet + Glue Data Catalog registration. Athena reads it the same
  way; Spark reads it the same way. The lab uses `glueparquet` because
  it wires the catalog table automatically.
- **Forgetting `Job.init` / `Job.commit`.** Without them, Glue's job
  bookmark state isn't updated, so a re-run re-processes everything
  even if nothing changed.
- **Configuring the Filter predicate wrong.** `status = 'active'` (with
  the equals sign) is Glue Studio's expression language. `status == 'active'`
  is Python and only works in the auto-generated script. Pick one.

## Going to production

Four things to add before this leaves a lab:

1. **Job bookmarks** — enable in the visual job's properties so re-runs
   only re-process changed partitions.
2. **Schema validation** — Glue Data Quality rules can assert
   `customer_id IS NOT NULL`, `created_at` parses as timestamp, etc.,
   BEFORE the curated output is written. Lab doesn't show this.
3. **Partitioning** — for fact tables >1 GB, add a partition key (e.g.,
   `DATE(created_at)`) so Athena queries can prune. Lab doesn't show this.
4. **Worker type tuning** — the lab uses 2 Standard workers ($0.44/DPU-h).
   G.1X is cheaper for streaming; G.2X is faster for memory-bound joins.

## Verification

The lab's "lab complete" check is: 9 active customers in
`curated_customers`, `status` column absent, `created_at` typed
`timestamp`, top-3 by `created_at` DESC = `[Leo, Kim, Ivan]`. The
driver and pytest suite exercise all four without AWS. The shell
scripts are the live-account equivalent.