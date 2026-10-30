# Setup Guide

> Everything in this course runs **locally with no GCP account, no credentials, and no bill**.
> The cloud sections are optional — read them when you want to deploy.

---

## The 5-minute path (no GCP required)

This is the path the course assumes. Everything in it works offline after the
first install.

```bash
cd data-engineering/data-Course/google/data-analysis

python3 -m venv .venv
source .venv/bin/activate

pip install -r project/requirements.txt

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Inspect the semantic layer
python project/local_bi.py describe
python project/local_bi.py explores

# Ask a question the way a dashboard would
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region,channel \
    --measures total_revenue,gross_margin,distinct_orders

# Run the validation gate
python project/local_bi.py validate --input ./sample_data/orders.csv
```

Expected `describe` output (excerpt):

```text
Model: orders
  label        : Orders
  table        : analytics.orders
  grain        : one row per order line
  primary key  : line_id
  description  : One row per order line. Note the grain: a single order with three lines appears three times.

  Measures:
    total_revenue            sum            additive       Sum of order line revenue.
    order_count              count          non-additive   Number of order lines. To count orders rather than lines, use count_distinct on order_id.
    distinct_orders          count_distinct non-additive   Number of unique orders.
    average_order_value      avg            additive       Average revenue per order line.
    gross_margin             sum            non-additive   Margin over revenue.
```

Expected `validate` output:

```text
Validation report
----------------------------------------------------
  source            : ./sample_data/orders.csv
  rows checked      : 901
  result            : FAIL
  findings:
    [ERROR  ] grain.not_unique: primary key 'line_id' is not unique: 1 value(s) repeat. Every measure over this table is inflated. (1 rows)
    [ERROR  ] freshness.stale: newest row in 'created_at' is 126 day(s) old; the limit is 2. The numbers are not current — say so on the dashboard. (1 rows)
    [WARNING] value.negative: 1 row(s) have a negative 'total_amount'. Legitimate for refunds; suspicious for a sign-flip bug. (1 rows)
```

The gate exits **1**. That is correct — the sample data is deliberately
imperfect, and the gate is doing its job.

### Python version

**3.10–3.13.** The course was developed and tested on **Python 3.11+**.
Check yours:

```bash
python3 --version
```

> **Why this matters.** The semantic layer in `project/core/` uses
> `from __future__ import annotations` and PEP 604 unions (`str | None`) in
> annotations. On 3.9 the `X | None` syntax in *annotations* still works
> (because of the future import) but not in runtime expressions like
> `isinstance(x, int | str)`.

---

## Installing the course tools

```bash
pip install -r project/requirements.txt
```

The core course needs **nothing but the standard library**. The
requirements file adds the tools you need for the optional parts:

| Package | Needed for |
|---|---|
| `pytest` | the test suite |
| `jupyter`, `nbclient`, `nbformat`, `ipykernel` | running the notebooks |
| `google-cloud-bigquery` | the optional BigQuery deployment section |
| `google-cloud-secretmanager` | the optional credential handling section |
| `psycopg2-binary` | the optional Postgres connector |

---

## The directory layout

```text
data-analysis/
├── README.md                   the course front door
├── chapters/                   seven chapters, the taught material
├── notebooks/                  six executable notebooks
├── interview/                  106 interview questions
├── resources/                  this guide, the cheatsheet, the linter
├── project/
│   ├── core/                   the semantic layer — pure stdlib
│   │   ├── model.py            models, measures, dimensions, explores
│   │   ├── date_helpers.py     the date spine and timeframes
│   │   ├── lookml.py           the LookML reader and writer
│   │   └── validate.py         the validation gate
│   ├── tests/                  145 tests
│   ├── local_bi.py             the CLI
│   ├── lookml/                 the rendered LookML
│   └── README.md               the project walkthrough
├── sample_data/                generated, deterministic
├── sql/                        the DDL and the reconciliation queries
└── out/                        scratch output
```

---

## Running everything

```bash
# The test suite — 145 tests, about two seconds
python -m pytest project/tests/ -q

# The course linter
python resources/audit_course.py

# Verify the notebooks match their builders
python resources/build_notebooks.py --check

# Execute every notebook, headless
python resources/run_notebooks.py

# The course's own structural tests
python resources/test_course.py
```

Expected results:

```text
145 passed in 2.21s
```

```text
==============================================================================
DATA ANALYSIS COURSE AUDIT
==============================================================================
ERRORS: 0   WARNINGS: 0   INFO: 0
```

---

## The CLI

```bash
python project/local_bi.py --help
```

| Command | What it does |
|---|---|
| `describe` | Print every model: grain, primary key, measures, dimensions, joins |
| `explores` | Print every explore and the fan-out risk of each join |
| `query` | Run a query against the local engine |
| `validate` | Run the validation gate; exits 1 on error |
| `spine` | Build a date spine and list the empty buckets |
| `spine-range` | Build a date spine over an explicit range |
| `lookml` | Render the semantic layer as LookML |

Useful flags:

```bash
# Write a query to a CSV
python project/local_bi.py query \
    --input ./sample_data/orders.csv \
    --dimensions region \
    --measures total_revenue \
    --format csv \
    --output ./out/revenue_by_region.csv

# Render the LookML with explores
python project/local_bi.py lookml --with-explores \
    --output project/lookml/ecommerce.model.lookml
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'model'`

The `core/` modules import each other by bare name, so `project/core` must
be on the path. The CLI handles this itself; if you are importing from a
notebook, add it:

```python
import sys
sys.path.insert(0, "project/core")
```

### `ModuleNotFoundError: No module named 'notebook_02'`

`resources/build_notebooks.py` imports the notebook builders from its own
directory. Run it as a script, not as a module:

```bash
python resources/build_notebooks.py
```

### The notebooks fail with `jupyter_client.kernelspec.NoSuchKernel`

Install the kernel:

```bash
pip install ipykernel
python -m ipykernel install --user --name=data-analysis-course
```

The notebook runner uses `python3` as the kernel name regardless, so this
is only needed if you open the notebooks in JupyterLab directly.

### The validation gate fails with `freshness.stale`

That is expected — the sample data is deliberately frozen 126 days in the
past so that the check fires. Pass `--max-age` to relax it, or ignore it:
the check is demonstrating itself.

### The sample data looks different from the chapters

Regenerate it. It is deterministic (`SEED = 42`), so a fresh run is
byte-identical:

```bash
python resources/sample_data.py --output-dir ./sample_data
```

If it is *still* different, you have a modified `sample_data.py` — check
`git diff resources/sample_data.py`.

---

## Optional: deploying to BigQuery

Nothing in the course requires this, but the DDL is written for BigQuery and
will run there.

```bash
pip install google-cloud-bigquery
gcloud auth application-default login
```

```bash
bq query --use_legacy_sql=false < sql/create_analytics.sql
bq query --use_legacy_sql=false < sql/reconciliation.sql
```

`sql/create_analytics.sql` creates four tables — `customers`, `products`,
`orders` and `date_spine` — with the grain recorded in the comments.

> **Note on the `date_spine`.** In BigQuery, prefer a table over a view for
> the spine: a view is recomputed on every query, and the spine is scanned
> on every query. The DDL creates it as a table so it can be materialised
> once per day.
