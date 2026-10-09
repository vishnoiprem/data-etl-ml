# Module 04 — Transformation

> **5 lessons · ~2.5 hours**

The "T" in ETL. This module covers the *middle* of the pipeline:
where the business logic lives. dbt-style SQL transforms, Python /
Spark transforms, joins and window functions, data quality, and
slowly changing dimensions.

Author: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**

---

## Lessons

| # | Lesson | What you'll learn |
|---|---|---|
| 14 | [dbt-style SQL Transformations](design/14_dbt_style_sql_transformations.md) | The medallion pattern: staging → intermediate → marts. |
| 15 | [Python/Spark Transformations](design/15_python_spark_transformations.md) | When SQL isn't enough: pandas, PySpark, vectorized. |
| 16 | [Aggregations, Joins, Window Functions](design/16_aggregations_joins_window_functions.md) | The three patterns every analyst needs. |
| 17 | [Data Quality](design/17_data_quality.md) | Great Expectations-style assertions, anomaly detection. |
| 18 | [Slowly Changing Dimensions](design/18_slowly_changing_dimensions.md) | SCD1 vs SCD2 vs SCD3 — when to use which. |

---

## Code

- [`code/sql_transforms.py`](code/sql_transforms.py) — five dbt-style
  models (`stg_*`, `int_*`, `fct_*`, `dim_*`) implemented as Python
  functions that run SQL against a `QueryRunner`.
- [`code/py_transforms.py`](code/py_transforms.py) — pure-Python
  (no pandas) transform utilities: dedup, normalize, enrich.
- [`code/data_quality.py`](code/data_quality.py) — Great
  Expectations-style assertion helpers that return True/False and
  log failures.
- [`tests/test_transforms.py`](tests/test_transforms.py) — 25+ unit
  tests.

---

## What this module is

The transformation layer is where the data becomes *useful*. Raw
events become star-schema marts. JSON payloads become typed
columns. Aggregations become daily KPIs. This module gives you
the vocabulary and the code for the most common patterns.
