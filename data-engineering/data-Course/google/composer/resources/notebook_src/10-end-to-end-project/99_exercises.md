## 9. Your turn

Six exercises on the whole project. Each one is a change you would actually make to a real pipeline.

### Exercise 1 — The missing Variable

A teammate deploys `03_etl_bigquery.py` to Composer and triggers it. The `check_source_exists` task fails with:

```
gsutil ls gs:///{{ ds }}/orders.csv
```

What is missing, where should it be set, and what is the *second* thing that will go wrong after you fix it?

### Exercise 2 — The midnight row

The source data starts including orders at exactly `2026-01-16T00:00:00+00:00`. Someone changes the aggregation filter from:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <  '{{ data_interval_end }}'
```

to:

```sql
WHERE order_ts >= '{{ data_interval_start }}'
  AND order_ts <= '{{ data_interval_end }}'
```

The run succeeds. What is wrong with the data now, and how many days until anyone notices?

### Exercise 3 — The branch that never fires

You deploy `04_branching_and_xcom.py` and trigger it with:

```json
{"row_count": 1500000, "force_full_load": false}
```

The `load_complete` task is **skipped**. `full_load` and `incremental_load` both show as skipped too, and `choose_strategy` shows as success.

What is wrong, and what is the one-word fix?

### Exercise 4 — The dangerous Variable

A teammate adds this to the DAG's `params`:

```python
params={
    "api_password": "hunter2",
    ...
}
```

List the three problems with this, and say where the value should live instead.

### Exercise 5 — The backfill that doubled everything

You backfill 2026-01-10 using the correct command. The 2026-01-10 partition now has **2490 rows** instead of 1245, and the region's revenue is exactly double.

Which line in `03_etl_bigquery.py` is responsible, and what is the one-word fix?

### Exercise 6 — Extend the project

Add a fifth task to `03_etl_bigquery.py`, between `load_to_bigquery` and `aggregate_by_region`, that writes the rejected rows to a dead-letter table `analytics.orders_rejected`.

Requirements:

1. It must be a `BigQueryInsertJobOperator` (or a `PythonOperator` — your choice, but say why).
2. It must not break the aggregation.
3. It must not break the idempotency property.

Write the code and say what happens to the table when the pipeline runs twice.
