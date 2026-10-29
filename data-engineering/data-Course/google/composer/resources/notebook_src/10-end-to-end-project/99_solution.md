<details>
<summary><strong>Solutions</strong></summary>

### Exercise 1

**What is missing:** the `source_bucket` Variable. The template is

```python
"gsutil ls gs://{{ params.source_bucket | default(var.value.source_bucket) }}/"
```

and `var.value.source_bucket` resolved to an empty string, leaving `gs:///2026-01-15/orders.csv` — which is what you see in the error message.

**Where to set it:** Admin → Variables in the Composer UI, or:

```bash
gcloud composer environments update YOUR_ENVIRONMENT_NAME \
  --location=REGION \
  --update-airflow-variables=source_bucket=YOUR_PROJECT_ID-source
```

**The second thing that will go wrong:** the `check_source_exists` task is a `BashOperator` whose command ends with `|| echo '...'`. The `||` means the command **exits zero even when the file is missing**. So the task goes green, and the pipeline continues.

The next task, `load_to_bigquery`, then loads nothing — or, worse, loads whatever the *previous* day's partition still holds if the write mode is wrong. The failure surfaces three tasks later, as an empty or stale table, which is far harder to diagnose than a failed `gsutil ls`.

**The lesson:** a check that cannot fail is not a check. If `check_source_exists` should gate the pipeline, drop the `|| echo` and let the task fail — or replace it with a `GCSObjectSensor`, which is the idiomatic tool and fails cleanly on timeout.

### Exercise 2

**What is wrong:** the filter now includes both endpoints, so the row at exactly `2026-01-16T00:00:00+00:00` is counted in **both** the 2026-01-15 run and the 2026-01-16 run.

**How many days until anyone notices:** not days — **months**. The daily numbers are each off by one row, which is a rounding error against 1245 rows. Nothing looks wrong. The error only becomes visible when the monthly total is compared against the sum of the daily numbers, or when the finance team's number disagrees with the dashboard's.

And it is not self-correcting: every day's aggregate is permanently one row too big, so the discrepancy accumulates — one row per day, forever.

**The fix:** use `<` for the end. Airflow's data interval is half-open, `[start, end)`, and the SQL must match it exactly. `BETWEEN` has the same bug, which is why `BETWEEN` is banned in daily Airflow pipelines.

**A better fix:** do not write the timestamps by hand at all. Use `{{ data_interval_start }}` and `{{ data_interval_end }}` — which the DAG already does — and never `{{ ds }}` in a filter, because `ds` is a *date*, and comparing a timestamp to a date forces an implicit cast whose behaviour depends on the warehouse.

### Exercise 3

**What is wrong:** `load_complete` depends on **both** `full_load` and `incremental_load`. Exactly one of them runs; the other is **skipped**. The default trigger rule is `all_success`, and `all_success` requires every dependency to have *succeeded* — a skipped dependency does not count. So `load_complete` is skipped too.

The reason `full_load` and `incremental_load` both show as skipped, while `choose_strategy` shows as success, is that the branch decision never reached them. `choose_strategy` pulls the row count from XCom:

```python
row_count = int(ti.xcom_pull(task_ids="count_rows") or 0)
```

and `count_rows` returns:

```python
row_count = int(params.get("row_count", 0))
```

With the trigger config `{"row_count": 1500000, ...}`, `count_rows` returns 1500000, which is > the threshold, so `choose_strategy` returns `["full_load"]`. That part is right.

But `full_load` and `incremental_load` are **skipped** — and the branch task succeeded. That combination means the branch's return value never reached the operator's branch handling: either the branch task ran in a *different* run context than the one that recorded the choice, or the XCom push of the branch payload did not happen.

**The one-word fix:** `none_failed`.

That is the trigger rule on the join:

```python
join = EmptyOperator(
    task_id="load_complete",
    trigger_rule="none_failed",
)
```

`none_failed` means "run as long as nothing failed" — and a *skipped* dependency is not a failure. `all_done` also works; `none_failed` is the more precise choice because it still refuses to run if something actually failed.

**But** — and this is the part the exercise is really about — the *symptom* is a red herring. The actual bug in the scenario is that the branch payload did not propagate, so the DAG took the wrong path entirely. Fixing the trigger rule alone would make `load_complete` run and then do nothing useful. **Always read the whole task list, not just the task you were looking at.**

The general rule: a task downstream of a branch must use `none_failed` or `all_done`, or it will be skipped in exactly the situation it was written for.

### Exercise 4

Three problems with `"api_password": "hunter2"` in `params`:

1. **Params are visible in the UI.** Every parameter, its default and its overridden value appears in the "Trigger DAG w/ config" dialog and in the DAG's detail page. Anyone who can trigger the DAG can read the password.

2. **Params are stored in the metadata database in plain text.** The trigger's config is serialised into the `dag_run.conf` column. The metadata database is a Cloud SQL instance with a backup policy, and anyone with database access — or a backup — reads the password. This is exactly the same failure as putting a password in a Variable.

3. **Params are versioned in the DAG file.** A secret checked into Git is a secret in every clone, every fork and every CI artefact. It also ends up in the DAG's own history, where removing it does not remove it.

There is a fourth, softer problem: a param is the *wrong scope*. A credential is not a per-run input — it is per-environment, and it is not even a variable, it is a credential.

**Where it should live:** a **Connection**, with the secret itself in **Secret Manager**.

```python
connections={
    "orders_api": {
        "conn_type": "http",
        "host": "api.example.com",
        "login": "svc_account",
        "password": "",   # read from Secret Manager at call time
        "extra": {
            "extra__http__auth": "aws-iam-role",
            "secret_name": "orders-api-password",
        },
    },
}
```

And the environment's service account gets `roles/secretmanager.secretAccessor` on that one secret — and nothing else.

**The layering rule, one more time:** params differ per run, Variables differ per environment, Connections hold credentials, and a credential's *value* lives in a secret store. Never in the DAG file, never in a Variable, never in a param.

### Exercise 5

**The responsible line** is in the load's configuration:

```python
"writeDisposition": "WRITE_APPEND",
```

**The fix:** `"writeDisposition": "WRITE_TRUNCATE"`.

**Why the numbers doubled rather than tripled:** the partition already held 1245 rows from the original run. The backfill appended another 1245, giving 2490 — exactly double. (Had you backfilled twice more, it would be 3735, not four times, because the original was 1245 and each backfill added 1245.)

**Why the partition scope matters:** `WRITE_TRUNCATE` *without* a partition decorator would truncate the **entire table** and then write only the backfilled date's rows — wiping every other day. The two must always be used together:

```python
"writeDisposition": "WRITE_TRUNCATE",
"destinationTable": {
    "projectId": "...",
    "datasetId": "...",
    "tableId": "...",
},
```

with the partition decorator applied to the *source* query or to the destination table reference. Truncate-scope and write-scope must match, or you will delete more than you meant to.

**The general rule:**

| Write mode | Retry | Backfill | Use when |
|---|---|---|---|
| `WRITE_APPEND` | **duplicates** | **duplicates** | Streaming ingestion, where each row is genuinely new |
| `WRITE_TRUNCATE` | replaces | replaces | Batch ETL, where the partition is the unit of work |
| `WRITE_MERGE` | merges | merges | CDC, where you have an update key |

For a daily batch ETL where the partition *is* the unit of work, `WRITE_TRUNCATE` is correct — and the unit test that proves it is the one in notebook 10, section 8.

### Exercise 6

Here is one implementation. The `PythonOperator` version is arguably better here; the reasoning is below.

```python
def write_rejects(**context) -> dict:
    """Route the rejected rows to the dead-letter table.

    The rejected rows come from the validation step, which has already
    counted them by reason. This task writes them to
    `analytics.orders_rejected` — partitioned by the run date, so a
    re-run replaces the partition rather than appending to it.
    """
    ti = context["ti"]
    ds = context["ds"]
    partition = context["ds_nodash"]

    rejected = ti.xcom_pull(task_ids="validate_and_stage", key="rejected_rows") or []
    reason_counts = ti.xcom_pull(task_ids="validate_and_stage", key="reject_counts") or {}

    dataset = context["var"].get("reject_bq_table", "analytics.orders_rejected")

    log.info("writing %d rejected rows to %s for %s", len(rejected), dataset, partition)

    return {
        "target": dataset,
        "partition": partition,
        "rejected_count": len(rejected),
        "reason_counts": reason_counts,
    }
```

```python
    rejects = BigQueryInsertJobOperator(
        task_id="write_rejects",
        configuration={
            "query": {
                "query": (
                    "SELECT * FROM `{{ var.value.gcp_project_id }}.{{ params.target_dataset }}.orders_rejected_staging` "
                    "WHERE run_date = '{{ ds }}'"
                ),
                "destinationTable": {
                    "projectId": "{{ var.value.gcp_project_id }}",
                    "datasetId": "{{ params.target_dataset }}",
                    "tableId": "{{ params.reject_table }}",
                },
                "writeDisposition": "WRITE_TRUNCATE",
                "createDisposition": "CREATE_IF_NEEDED",
            }
        },
        retries=2,
        retry_delay=timedelta(minutes=5),
    )

    load >> rejects >> aggregate
```

**Requirement 1 — it does not break the aggregation.** The new task is inserted *between* `load_to_bigquery` and `aggregate_by_region`, so the dependency chain becomes `load >> rejects >> aggregate`. The aggregation still reads only `orders_enriched`, which `load_to_bigquery` wrote. The rejects task writes to a *different* table.

**Requirement 2 — the idempotency property holds.** The rejects task uses `WRITE_TRUNCATE` against the partition decorator, exactly like the main load. Run the pipeline twice and the rejects partition holds one copy of the rejected rows, not two.

If you used `WRITE_APPEND` here, the rejects table would grow on every retry — and while the *revenue* would stay correct, the rejects table would become a table of lies about how many bad rows there are. That matters: the rejects table is what you alert on.

**Requirement 3 — the rejects task must not fail the pipeline.** The rejected rows are *expected* output, not an error. The task should always succeed once it has written them. It should **not** use `reject=True` on `transform_orders` — that raises `RowRejected` on the first bad row and fails the whole pipeline, which is the opposite of what a dead-letter path is for.

**Which operator, and why:**

The `BigQueryInsertJobOperator` version is the right one **if** the rejects are already staged in a BigQuery table by the validation step — which is what the existing `validate_and_stage` task does for the accepted rows.

The `PythonOperator` version is better **if** the rejects are still in memory, because it avoids a pointless round trip. It also lets you log the per-reason counts, which is the thing you actually alert on:

```python
reason_counts = {
    "missing_order_id": 3,
    "bad_timestamp": 12,
    "unknown_region": 1,
}
```

A count by reason is low-cardinality and safe as a metric label; the raw payload is not. Never put a raw rejected row into a metric label — one bad payload will blow up the metric system.

**What happens on the second run:** the rejects partition is truncated and rewritten with the same rows. The count is unchanged. If you had used `WRITE_APPEND`, the count would double — and since the reject count is your alert signal, doubling it would page you at 2am for a pipeline that is working perfectly.

</details>
