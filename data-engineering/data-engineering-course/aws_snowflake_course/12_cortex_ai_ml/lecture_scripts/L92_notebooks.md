---
l_id: L92
title: Snowflake Notebooks
duration: "6:00"
prereqs: ["L91 - Snowflake ML"]
---

# L92 — Snowflake Notebooks

> **Author:** Prem Vishnoi &lt;pvishnoi&commat;avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 6:00

## Prereqs

A role with `USAGE` on a warehouse and a database where the
notebook will live.

## Lecture

Snowflake Notebooks are a **Jupyter-compatible Python IDE inside
Snowflake**. Cells run against a live Snowpark session, so
DataFrames you build reference real tables, and any `model.fit(...)`
trains on warehouse compute — no copy-paste to your laptop.

### Create a notebook

From the Snowflake UI: `Projects → Notebooks → + Notebook → From
SQL`. Or via SQL:

```sql
CREATE NOTEBOOK ml.fraud_modeling
  FROM '@ml.notebooks/fraud_modeling.ipynb'
  MAIN_FILE = 'fraud_modeling.ipynb'
  QUERY_WAREHOUSE = 'compute_wh';
```

The notebook is just a file in a stage; the `NOTEBOOK` object is
the metadata that wires it up to a warehouse.

### The default cell

```python
# Standard header — every cell gets a Snowpark session
from snowflake.snowpark.context import get_active_session
session = get_active_session()

# Quick sanity
print(session.sql("SELECT CURRENT_ACCOUNT()").collect())
```

### Pulling data

```python
df = session.table("analytics.gold.fct_transactions_labeled")
df.show()
```

The cell executes a SQL `SELECT` on the warehouse, returns a
Snowpark `DataFrame`, and renders the first 50 rows.

### Mixing SQL and Python

A notebook is more than Python — you can have a SQL cell directly:

```sql
-- %%sql magic (or "SQL" cell type)
SELECT merchant_cat, COUNT(*) AS n, AVG(is_fraud) AS fraud_rate
FROM analytics.gold.fct_transactions_labeled
GROUP BY 1
ORDER BY 3 DESC;
```

### Scheduling

A notebook can be scheduled like a Task:

```sql
ALTER NOTEBOOK ml.fraud_modeling
  ADD SCHEDULE 'USING CRON 0 6 * * * America/Los_Angeles'
  WAREHOUSE = compute_wh;
```

The notebook re-runs end-to-end on the schedule. Cells that produce
tables (e.g. a `CREATE TABLE ... AS SELECT ...`) will refresh
those tables on each run.

### Versioning

Notebooks live in git-backed stages; the Snowflake UI has
"Version history" → restore prior versions. For serious
versioning, mount the stage to a git repo and use your normal
branch / PR flow.

### When to use a notebook vs a worksheet vs a Task

| Surface | Best for |
|---|---|
| Worksheet | Ad-hoc SQL exploration. |
| Notebook | Python exploration + ML training + visualization. |
| Task | Scheduled, headless data or model refresh. |

## Key takeaways

- Notebooks are Jupyter-compatible Python with a live Snowpark
  session.
- They support both Python and SQL cells in the same file.
- You can schedule them like a Task, with the notebook itself
  as the procedure body.

## What's next

In **L93 — Streamlit in Snowflake** we move from notebooks to
apps — the same Snowpark session, but with `st.write(...)` and
widgets instead of cells.
