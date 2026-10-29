<details>
<summary><strong>Solutions</strong></summary>

### Exercise 1

**A** has two problems the validator will catch, and one it will not.

The two it catches:

- **The service account is not scoped.** `acme-dev@acme.iam.gserviceaccount.com` is fine as a string (it has an `@`), but there is no dedicated account *and* no roles declared — a dev environment running as a shared identity with prod's blast radius. Fix: create `composer-dev@acme.iam.gserviceaccount.com` and grant `roles/composer.worker`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`, `roles/cloudresourcemanager.projectViewer`.
- **`log_retention_days` and `dag_retention_days` are defaults (30) but `bucket_regions` is empty**, so the validator cannot confirm the buckets are in `europe-west1`. Fix: declare `bucket_regions={"gs://acme-dev-dags": "europe-west1", "gs://acme-dev-logs": "europe-west1"}`.

The one it will not catch: **`MEDIUM` for a dev environment.** The cost model shows a `MEDIUM` environment costs $340/month whether it runs 25% of the time or 100%. A dev environment usually runs a handful of DAGs a day. Fix: `size="SMALL"` (1–2 workers), which cuts the fixed monthly cost from $340 to $180 and saves $160/month for a $0 material difference in capability. A dev environment does not need `AIRFLOW__CORE__PARALLELISM=32`.

**B** has three problems, and the first is the one that ends a career.

- **The DAG bucket and the log bucket are the same bucket.** The validator says it exactly:

  ```
  ! the DAG bucket and the log bucket must be different — the log
    lifecycle would delete your DAG files
  ```

  The moment you put a lifecycle rule on the logs (you will — see Exercise 5), the rule matches the shared prefix and Composer cannot find the DAG files. Every DAG vanishes from the UI and the scheduler log fills with `FileNotFoundError`. Fix: two buckets, always.

- **`env_vars={}` — no `AIRFLOW__CORE__DEFAULT_TIMEZONE`.** The validator catches it:

  ```
  ! AIRFLOW__CORE__DEFAULT_TIMEZONE is not set — set it explicitly to
    UTC so the scheduler and the warehouse agree
  ```

  Without it, the environment inherits the default timezone, and a daily ETL whose source data lands at 23:30 UTC will partition into the wrong day. Fix: `env_vars={"AIRFLOW__CORE__DEFAULT_TIMEZONE": "UTC"}`.

- **Composer 3 on a `SMALL` environment.** The validator catches it:

  ```
  ! Composer 3 with a SMALL environment has 1-2 workers, each paying a
    ~45s pod startup — check the task durations
  ```

  Each task pays ~45 s of pod startup. If the DAGs are chatty chains, that tax is paid sequentially, task after task. Fix: either Composer 2, or Composer 3 on `MEDIUM` with long-running tasks.

### Exercise 2

**Composer 3** — because of the Spark job.

The reasoning, task by task:

| Task | Duration | Verdict |
|---|---|---|
| 3-minute Parquet write | 3 min | Wrong for Composer 3 — the 45 s pod startup is 25% of the task's wall time |
| 25-minute BigQuery query | 25 min | Composer 3 is fine; a query this long benefits from its own resources |
| 4-minute REST call | 4 min | Wrong for Composer 3 — startup is 19% overhead |
| 40-minute Spark submit | 40 min | **Composer 3, clearly** — a Spark task wants its own node, its own image and its own memory |

A single environment runs one executor. If the Spark task needs a Kubernetes-native pod with a Spark image and 32 GB, the environment must be `composer-3`. The short tasks then pay the startup tax — but 45 s against a 3-minute task is an acceptable price for one environment that can run everything.

**The crossover:** the task duration at which the 45 s pod tax is below 10% of the total.

```
crossover = 45 / 0.10 - 45 = 405 seconds = 6.8 minutes
```

So: **roughly 7 minutes.** Below that, the pod startup dominates and Celery (Composer 2, ~1 s dispatch) is the better executor. Above it, the tax is noise.

And note the crossover is not a cliff — it is a *margin* argument. If you would accept a 25% overhead, the crossover drops to 60 s of task duration, and Composer 2 is almost never the wrong answer for a chatty DAG.

### Exercise 3

```python
PROD = ComposerEnvironment(
    name="analytics-prod",
    location="europe-west1",
    generation="composer-2",
    size="MEDIUM",
    machine_type="n1-standard-2",
    dag_bucket="gs://acme-prod-dags",
    log_bucket="gs://acme-prod-logs",
    service_account="composer-prod@acme.iam.gserviceaccount.com",
    oauth_scope="cloud-platform",
    python_version="3.11",
    env_vars={
        "AIRFLOW__CORE__DEFAULT_TIMEZONE": "UTC",
        "AIRFLOW__CORE__PARALLELISM": "32",
    },
    variables={
        "gcp_project_id": "acme",
        "source_bucket": "acme-source",
        "bq_dataset": "analytics",
        "bq_table": "orders_enriched",
    },
    log_retention_days=30,
    dag_retention_days=2,
    bucket_regions={
        "gs://acme-prod-dags": "europe-west1",
        "gs://acme-prod-logs": "europe-west1",
    },
)

print(PROD.validate())
print()
print(PROD.create_command())
```

`validate()` returns `[]` — no problems. The rendered command:

```
gcloud composer environments create analytics-prod \
  --location=europe-west1 \
  --image-version=composer-2.9.3-airflow-2.9.3 \
  --environment-size=ENVIRONMENT_SIZE_MEDIUM \
  --machine-type=n1-standard-2 \
  --dag-bucket=gs://acme-prod-dags \
  --log-bucket=gs://acme-prod-logs \
  --oauth-scope=cloud-platform \
  --python-version=3.11 \
  --service-account=composer-prod@acme.iam.gserviceaccount.com \
  --env-vars=AIRFLOW__CORE__DEFAULT_TIMEZONE=UTC,AIRFLOW__CORE__PARALLELISM=32
```

The Variables are set separately, after creation — `--update-airflow-variables` on `environments create` works but is easier to audit as its own step, and it is how you can re-apply them idempotently:

```
gcloud composer environments update analytics-prod --location=europe-west1 --update-airflow-variables=bq_dataset=analytics
gcloud composer environments update analytics-prod --location=europe-west1 --update-airflow-variables=bq_table=orders_enriched
gcloud composer environments update analytics-prod --location=europe-west1 --update-airflow-variables=gcp_project_id=acme
gcloud composer environments update analytics-prod --location=europe-west1 --update-airflow-variables=source_bucket=acme-source
```

Note the two-day DAG retention: the DAG files are in Git, so the bucket only needs to hold the current version. Thirty days of *log* retention is generous enough to debug a monthly report.

### Exercise 4

**1. Password in `extra`:**

```python
connections={
    "orders_api": {
        "conn_type": "http",
        "host": "api.example.com",
        "login": "svc_account",
        "password": "s3cr3t",
        "extra": "{}",
    },
}
```

**2. Pointing `extra` at Secret Manager:**

```python
connections={
    "orders_api": {
        "conn_type": "http",
        "host": "api.example.com",
        "login": "svc_account",
        "password": "",
        "extra": {
            "extra__http__auth": "aws-iam-role",
            "secret_name": "orders-api-password",
        },
    },
}
```

**Ship version 2.** Version 1 puts the password in the Airflow metadata database in plain text, visible in the UI to anyone with Connection read access, and versioned in the audit log every time it is edited.

Version 2 keeps the secret in Secret Manager — versioned, auditable, rotatable without touching the DAG, and revocable without touching the Airflow environment at all. The service account needs `roles/secretmanager.secretAccessor` on that one secret, and nothing else.

The general principle: **the Connection holds *where* the credential is; the secret store holds the credential.**

### Exercise 5

The teardown, in order:

**Step 1 — export what matters.** The DAGs are in Git, so nothing to export there. The run history lives in the Cloud SQL metadata database, which the next step destroys. If anyone will ever ask "did the January 15 run succeed?", take a snapshot:

```bash
gcloud sql export sql INSTANCES_ID gs://acme-backups/metadata-$(date +%F).sql --project=acme
```

**Step 2 — delete the environment.**

```bash
gcloud composer environments delete analytics-prod --location=europe-west1
```

This destroys the GKE cluster, the Cloud SQL instance (with all run history, XComs, Variables and Connections), the web server, the scheduler, and Composer-managed identities.

**Step 3 — wait for `DELETED`.** Not `DELETING`. While it is `DELETING`, the Cloud SQL instance is still billing.

```bash
gcloud composer environments describe analytics-prod --location=europe-west1 --format="value(state)"
```

**Step 4 — delete the log bucket.** 200 GB of logs, and no lifecycle rule means nobody will delete them for you.

```bash
gsutil rm -r gs://acme-prod-logs
```

**Step 5 — the DAG bucket.** The DAGs are in Git, so the bucket is disposable. But verify the sync is working *before* you delete it — a bucket with the DAGs and no Git history is the only copy:

```bash
gsutil ls gs://acme-prod-dags
```

**Step 6 — the service account and its bindings.** The bindings are project-level and do **not** die with the environment, so remove them explicitly, then delete the account:

```bash
gcloud projects remove-iam-policy-binding acme \
  --member="serviceAccount:composer-prod@acme.iam.gserviceaccount.com" \
  --role="roles/composer.worker"
# ... and the other three

gcloud iam service-accounts delete composer-prod@acme.iam.gserviceaccount.com
```

**Step 7 — the VPC.** The VPC, subnets and Cloud NAT are project resources and survive. If they were created for this environment alone, delete them too — but check first whether anything else uses them.

**Step 8 — verify the bill.** The next day's usage report is the only proof that the money stopped.

**Survival table:**

| Resource | Survives? |
|---|---|
| GKE cluster | No — destroyed |
| Cloud SQL metadata DB | No — destroyed (snapshot first if you need history) |
| Web server / scheduler | No — destroyed |
| DAG bucket | **Yes** — yours; delete manually if Git is the source of truth |
| Log bucket | **Yes** — yours; delete manually |
| BigQuery tables | **Yes** — not a Composer resource |
| IAM bindings | **Yes** — remove them explicitly |
| Service account | Sometimes — Composer deletes it only if it created it |
| VPC / subnets / Cloud NAT | **Yes** — project resources |

### Exercise 6

**1. Total monthly cost of the three environments.**

Using the model from section 4 (`monthly_cost(spec, utilisation=u)`), with the `MEDIUM` spec's worker midpoint of 4.5 workers:

| Environment | Utilisation | Workers | Total/month |
|---|---|---|---|
| dev | 25% | 1.125 | $186.25 |
| staging | 50% | 2.25 | $221.48 |
| prod | 100% | 4.5 | $340.00 |
| **Total** | | | **$747.73** |

**2. One `MEDIUM` environment at 100% utilisation.** **$340.00/month.**

**3. Annual saving from consolidating.** $(747.73 - 340.00) \times 12 = **$4,892.76/year.**

**Why it is not the difference you might expect.**

A naive calculation assumes the cost scales with usage: dev is cheap because it is used a quarter of the time, so merging should save three-quarters of dev's cost. It does not, because **the fixed components do not shrink with usage**.

For a `MEDIUM` environment, the fixed monthly cost is $340 — and the workers' variable compute is a *small* part of the bill. At 25% utilisation the bill is $186.25, so the fixed floor for a `MEDIUM` environment is roughly $175–180/month of pure "being switched on". The variable worker compute at 25% utilisation is only about $6 of that.

So the saving from deleting a `MEDIUM` environment is roughly **$186** — you eliminate the web server, the scheduler, the Cloud SQL instance and the GKE control plane, and you keep the small amount of worker compute by folding it into the surviving environment.

The deeper lesson is the same one from the utilisation table in section 4: **an idle environment is not free, and it is not cheap either.** The 25%-utilised dev environment costs 55% of a fully-utilised one, because the always-on half of the bill is fixed. That is why the rule is "one environment per team, sized for the peak" — not "one environment per project, per stage, per team".

And the caveat: consolidation only works if the DAGs are compatible. A dev environment that runs a broken DAG should not be able to break prod, and prod's data should not be visible to someone who is debugging. If you need that separation, you need separate environments, and you accept the $186/month floor as the price of the isolation.

</details>
