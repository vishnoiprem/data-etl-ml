## 8. Your turn

Six exercises on Composer environments. Each one is a change you would actually make; each has a short answer.

### Exercise 1 — Spot the two environment descriptions that will cost you money

You inherit two environments. Read each and name the specific problem, and the specific fix.

**A.**

```python
ComposerEnvironment(
    name="analytics-dev",
    location="europe-west1",
    generation="composer-2",
    size="MEDIUM",
    dag_bucket="gs://acme-dev-dags",
    log_bucket="gs://acme-dev-logs",
    service_account="acme-dev@acme.iam.gserviceaccount.com",
    env_vars={"AIRFLOW__CORE__DEFAULT_TIMEZONE": "UTC"},
)
```

**B.**

```python
ComposerEnvironment(
    name="analytics-prod",
    location="us-central1",
    generation="composer-3",
    size="SMALL",
    dag_bucket="gs://acme-prod-logs",
    log_bucket="gs://acme-prod-logs",
    service_account="acme-prod@acme.iam.gserviceaccount.com",
    env_vars={},
)
```

### Exercise 2 — Choose the generation

Your DAGs have these task shapes:

- a 3-minute `PythonOperator` that reads a 40 MB CSV and writes a Parquet file
- a 25-minute `BigQueryOperator` that runs a heavy SQL query
- a 4-minute `PythonOperator` that calls a REST API and writes one row
- a 40-minute `SparkSubmitOperator` on a 32 GB dataset

Which Composer generation do you pick, and why? What is the crossover task duration you would use to justify it?

### Exercise 3 — Write the environment description

Write the `ComposerEnvironment` dataclass instance for a production environment with these requirements:

- location `europe-west1`, Composer 2, `MEDIUM`, `n1-standard-2`
- DAG bucket `gs://acme-prod-dags`, log bucket `gs://acme-prod-logs`, both in `europe-west1`
- service account `composer-prod@acme.iam.gserviceaccount.com`
- `AIRFLOW__CORE__DEFAULT_TIMEZONE=UTC`, `AIRFLOW__CORE__PARALLELISM=32`
- 30 days of log retention
- Variables: `gcp_project_id`, `source_bucket`, `bq_dataset`, `bq_table`
- 2-day DAG retention

Then call `.validate()` and `.create_command()` on it.

### Exercise 4 — The connection that should not be a Variable

A DAG reads an API password. Write it as:

1. a Connection with the password in `extra`
2. a Connection whose `extra` points at Secret Manager

Say which one you would ship and why, in one sentence each.

### Exercise 5 — Teardown order

You are decommissioning a `MEDIUM` environment in `europe-west1`. Its DAGs live in Git. Its logs bucket has 200 GB in it. Its service account has four project-level role bindings.

Write the teardown steps in the correct order, and state for each resource whether it survives the environment deletion.

### Exercise 6 — Budget the environment

A `MEDIUM` environment costs $340/month at full utilisation. The team wants three environments (dev, staging, prod). Their utilisation is 25%, 50% and 100% respectively.

Using the cost model from section 4:

1. What is the total monthly cost of the three environments together?
2. What would the total be if all three DAG sets ran in a single `MEDIUM` environment at 100% utilisation?
3. What is the annual saving from consolidating?

Explain, in one paragraph, why the answer is not the difference you might expect.
