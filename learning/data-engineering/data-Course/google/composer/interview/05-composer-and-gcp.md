# Module 5 — Composer & GCP

> **12 questions · Module 5 · Composer provisioning, environment sizing, versions, UI, IAM, cleanup/billing, Composer vs self-managed Airflow**

---

## Provisioning an environment

### 1. What does `gcloud composer environments create` actually build, and what does Google manage?

**It builds a managed Airflow deployment: web server, scheduler, worker pool, a Cloud SQL Postgres instance for the metadata database, and a GCS bucket holding your DAG files.**

```bash
gcloud composer environments create my-env \
  --location=us-central1 \
  --environment-size=ENVIRONMENT_SIZE_SMALL \
  --image-version=composer-2.9.3-airflow-2.9.3
```

The pieces and who owns them:

| Piece | What it is | Managed by Google |
|---|---|---|
| **DAG bucket** | GCS bucket where your DAG `.py` files live | yes (created for you, unless you supply your own) |
| **Scheduler** | the polling loop that creates runs and queues tasks | yes |
| **Web server** | the Airflow UI + REST API — **this *is* the Composer UI** | yes |
| **Workers** | the Celery worker pool that runs task callables | yes, you size it |
| **Metadata DB** | Cloud SQL Postgres: `dag`, `task`, `dag_run`, `task_instance`, `xcom`, `variable`, `connection` | yes, you size it |
| **Airflow CLI** | `airflow` inside the environment — `airflow dags list`, `airflow dags backfill`, `airflow dags test` | yes |

Two consequences that follow immediately:

- **The DAG file is the deployable artefact.** You upload `.py` files to the DAG bucket; Composer parses them within 1–3 minutes. There is no build step and no image.
- **You do not get to change most of the internals.** The executor, the broker, the scheduler topology, and the metadata DB are managed. What you control is the *size*, the *version*, the *config*, the *DAGs*, and the *IAM*.

**The failure story:** a team deployed DAGs by uploading them to a GCS bucket they created themselves, rather than the Composer-managed one, and never noticed for 6 weeks. Composer was parsing the managed bucket, which was empty; the team's bucket just accumulated files. The DAGs appeared "in GCS" and "in the repo" but never ran. Composer does not parse arbitrary buckets.

### 2. How does the DAG actually get from your laptop into the environment, and what are the three ways to do it?

**Three ways, and they differ in what you get for review and reproducibility.**

1. **`gcloud storage cp`** — the direct route, and what you use while developing:

```bash
gcloud storage cp project/dags/*.py gs://<composer-dags-bucket>/dags/
```

2. **Git-sync** — point Composer at a Git repository, and it syncs on a schedule or on push. You get a commit SHA per environment update, which is what makes "which code produced this run?" answerable.

3. **CI/CD** — a pipeline that tests the DAGs, then uploads them. This is what you want once more than one person touches the DAGs.

The mechanism once the file is in the bucket is the **DAG processor**: it lists the folder, imports each `.py` as a module (with a module cache keyed by path and mtime, so an unchanged file is not re-imported), collects the `DAG` objects, and writes the `dag`/`task` rows.

Two things to know about the import:

- **Your DAG file is executed as Python, at parse time, on the scheduler.** Any top-level code runs every parse cycle. Keep it cheap and side-effect free.
- **The DAG folder and your core module must be siblings in the same uploaded package.** `from pipeline_logic import transform_orders` fails with `ImportError: cannot import name 'transform_orders' from 'pipeline_logic'` unless you upload the whole tree.

```text
dags/
  dag_config.py
  pipeline_logic.py
  03_etl_bigquery.py
```

**The failure story:** a developer uploaded a single DAG file with `gsutil cp`. The DAG never appeared — the `ImportError` was recorded in the `import_error` table and visible only in the Composer UI's DAG-file detail view, which nobody was looking at. The fix was uploading the whole `dags/` tree, plus a CI step that runs `DagBag` and fails on `bag.import_errors`.

### 3. What is the DAG bucket, what happens to it when you delete the environment, and how do you keep your code?

**The DAG bucket is a GCS bucket that Composer creates for you and parses.** It holds your DAG `.py` files.

**The critical operational fact: deleting a Composer environment deletes the Composer-managed DAG bucket and its contents — unless you supply your own bucket at creation time.** That is the difference between "delete the environment" and "lose every DAG file you ever wrote".

So there are two provisioning strategies:

| | Composer-managed bucket | Your own bucket |
|---|---|---|
| Setup | simpler | you create it, name it, apply a retention policy |
| Deleting the environment | **the bucket and the DAGs are deleted** | your bucket survives |
| Sharing DAGs across environments | copy them | point both environments at it |
| Lifecycle | disposable | you own it |

The safe pattern is: **your DAGs live in Git; the Composer bucket is a deployment target.** Then deleting an environment is a non-event, and the "what was running last Tuesday?" question is answered by `git log`.

If you must use the Composer-managed bucket, export before deleting:

```bash
gcloud storage cp -r gs://<composer-dags-bucket>/dags/ ./backup-dags-$(date +%Y%m%d)/
```

**The failure story:** a team deleted a Composer environment during a cost-cutting exercise and did not notice the DAG bucket went with it. The DAG files had never been in Git — they were edited directly in the Composer UI's DAG editor (which exists and is convenient and is a trap). Two months later they wanted to recreate the environment and had to rewrite 34 DAG files from memory and screenshots. The fix was a mandatory policy: no DAG edits in the UI, Git from day one.

### 4. What is `gcloud composer environments update` for, and what are the operations that are genuinely safe to do on a live environment?

**`update` handles version bumps, size changes, config changes, and label changes — in place, on the running environment.** The Composer UI has the same operations under **Environment → Edit**.

| Operation | Safe on a live environment? | Notes |
|---|---|---|
| **Config change** (connections, variables via config, env vars) | yes | takes effect on the next task run |
| **Size change** | yes, with care | scales workers up or down; a scale-down can pre-empt running tasks |
| **Airflow version bump** | **with care** | this is the one that breaks DAGs — see Q6 |
| **Label change** | yes | metadata only |
| **Adding a Python dependency** | yes | requires a new image version, not `update` alone |
| **Deleting** | destroys the bucket | export first |

The scale-down case is the one that surprises people: reducing the worker count while tasks are running can cause worker pre-emption, which — per the at-least-once model — means the task runs again. If the task is not idempotent, that is corruption.

**The failure story:** a team scaled an environment down from 8 workers to 3 during a quiet period, to save money. Two DAGs had long-running tasks in flight; the workers were pre-empted and the tasks were requeued and re-run. One of them was a non-idempotent `WRITE_APPEND` load, so the day's rows were written twice. The fix was to only scale down during a maintenance window with the schedule paused, and to audit for idempotency before reducing capacity.

### 5. How do you delete a Composer environment cleanly, and what are the things that survive?

**The delete sequence, and what is destroyed versus what is not:**

```bash
gcloud composer environments delete my-env \
  --location=us-central1 \
  --quiet
```

What is **destroyed**:

- The Composer-managed **DAG bucket** and every DAG file in it.
- The **web server**, **scheduler**, and **workers**.
- The **Airflow metadata database** — but this is the Cloud SQL instance Composer created for the environment. The course's chapter on Composer describes it as part of the environment; in practice, verify whether the instance is Composer-managed and deleted with the environment or is a customer-managed instance you supplied.

What **survives**:

- **Your BigQuery tables and datasets.** These are yours; the environment only had access to them.
- **Your GCS buckets**, other than the DAG bucket.
- **Your DAG files, if they are in Git** or in a bucket you supplied.
- **Your code, if it is in Git.** This is the whole point of the previous section.

**Before deleting, take three things:**

1. A DAG export — `gcloud storage cp -r gs://<dags-bucket>/dags/ ./backup/`, or just confirm Git has it.
2. The list of Connections and Variables — `airflow connections list`, `airflow variables list` inside the environment. These are in the metadata DB and go with it.
3. The list of Airflow version and image version — `gcloud composer environments describe my-env --location=us-central1`. You need this to recreate it identically.

**The failure story:** a team deleted a Composer environment and, four months later, needed to recreate it for an audit. The Connections were gone — including the BigQuery service-account connection — and the DAGs were gone. They had to recreate the credentials from scratch and re-derive which IAM roles the environment needed. The fix was a documented "environment spec" file in Git listing the image version, size, config, connections, variables, and IAM roles, updated whenever the environment changed. That file is now the source of truth for recreating the environment.

---

## Versions and sizing

### 6. What do the Composer image versions mean, and why is a version bump the most dangerous operation you can perform?

**A Composer image version pins both the Airflow version and the image variant.** The naming is `composer-<composer-version>-airflow-<airflow-version>`, e.g. `composer-2.9.3-airflow-2.9.3`. Composer 2 environments pin Airflow 2.x releases such as 2.8.2, 2.9.3, and 2.10.x; Composer 3 environments are the newer GKE-based generation.

The critical fact: **the image version determines the Airflow version, and Airflow versions carry breaking changes.** The ones that bite in a 2.x upgrade:

| Change | Version | What breaks |
|---|---|---|
| `schedule_interval` → `schedule` | 2.4 | `schedule_interval` still works but warns; removed in Airflow 3 |
| `logical_date` replaces `execution_date` | 2.2 | `dag.test(execution_date=...)` → `logical_date` in newer versions |
| Datasets replace data-aware scheduling | 2.4 | `schedule=[dataset]` semantics |
| `DummyOperator` deprecated | 2.x | removed in Airflow 3 — use `EmptyOperator` |
| `GCSOperator` renamed | 2.x | `GCSUploadOperator` / `GCSDownloadOperator` |
| `SubDagOperator` removed | 2.0 | use dynamic task mapping instead |
| `SequentialExecutor` removed | 2.0 | — |
| `extra` not encrypted | 2.x | `extra` was never encrypted; `password` is |

**This is exactly what Environment Versioning is for.** Composer lets you clone an environment, bump the version on the *copy*, and test there — leaving production on its pinned Airflow version until you are confident. The course's phrasing: *"you can pin Airflow 2.9.3 while you test 2.10 on a copy."*

**The failure story:** a team upgraded a production Composer environment from Airflow 2.6.3 to 2.8.2 in place, on a Friday, with 40 DAGs. Two broke: one used `schedule_interval` (deprecated but working — that one survived), and one used a custom operator that subclassed a `BaseOperator` whose `apply_defaults` handling changed. The DAG failed to import, so it **vanished from the UI** — and the team did not notice for 4 days because nothing alerted on "DAG count decreased". The fix was to clone the environment, upgrade the clone, run the DAG structure tests against the clone's Airflow version, and only then promote. The new permanent check was: *the number of DAGs in the environment is itself an alert*.

### 7. How do you size a Composer environment, and what does the size actually control?

**The size controls the worker pool and the Cloud SQL instance shape** — the two things that scale with your workload.

| Size | Workers | Typical use |
|---|---|---|
| Small | 1–2 | a handful of light DAGs, mostly BigQuery queries |
| Medium | 3–6 | a normal team environment, some Python tasks |
| Large | 7–15 | many concurrent tasks, sensors, heavier Python |
| Custom | your numbers | when you have measured the requirement |

**The sizing rule from the course:** *if your Airflow DAG is mostly issuing queries, size the Composer environment small.* A `BigQueryExecuteQueryOperator` runs server-side — the worker only issues the job and waits. **If your DAG is mostly running Python, size it for the concurrency you need.**

The reasoning: a Composer environment is a roughly fixed monthly cost. A small environment with a couple of workers costs a few hundred dollars a month; a large one with many workers costs several thousand. **The job compute dwarfs this — but only if you are running compute.** If you are running BigQuery queries through Airflow, the environment cost is a larger share of the total, and the question becomes "how many workers do I need to run my queries?" — usually not many.

The other thing sizing affects is the **concurrency ceiling**. The environment-wide `parallelism` setting and the worker pool together cap how many task instances can run at once. That is why a DAG with 50 poke-mode sensors can starve a DAG with 3 tasks — **worker sizing is per-environment, not per-DAG.**

**The failure story:** a team sized their environment Large (12 workers) because two DAGs had long-running Python tasks. They then migrated 30 of their 40 workflows to BigQuery scheduled queries, which need almost no workers. The environment was still costing $900/month for 12 workers that were idle 22 hours a day. They dropped to Small (2 workers) and the bill fell to $280/month — the two heavy DAGs still fit, because they ran sequentially at 02:00 and used two workers.

### 8. Where does the `airflow` CLI fit in, and what should you actually run with it?

**The `airflow` CLI is available inside the Composer environment**, and it is the same Airflow CLI you would use on a self-managed install. In Composer you get to it through the environment's web-server/worker pods:

```bash
gcloud composer environments run my-env \
  --location=us-central1 \
  --command "airflow dags list"
```

Useful commands:

```bash
airflow dags list                       # what the scheduler sees
airflow dags list-import-errors          # the import_error table
airflow dags backfill my_dag -s 2026-01-01 -e 2026-01-07
airflow dags trigger my_dag --conf '{"force_full_load": true}'
airflow dags test my_dag 2026-01-15     # run one logical date (2.5+)
airflow tasks states-for-dag-run my_dag 2026-01-15
airflow connections list
airflow variables list
```

**What the CLI is best for:** reading state you cannot see in the UI (import errors, task instance states for a specific run), running a backfill, and triggering with a `--conf`.

**What it is *not*:** a deployment mechanism. Do not use `airflow dags deploy` — in Composer, deployment is uploading to the DAG bucket. And `airflow dags test` in a Composer environment runs the **real operators** against real GCP, so it writes real data.

**The failure story:** a team ran `airflow dags test etl_orders_to_bigquery 2026-01-15` inside a Composer environment pointed at production. The DAG's `BigQueryInsertJobOperator` used `WRITE_APPEND` without a partition decorator, so the test wrote 1,245 rows into the production table for a logical date the live pipeline was about to process. The live run appended them again. The fix was a standing rule: **`airflow dags test` only against a dev dataset**, enforced by a `params`-driven `target_dataset` that defaults to a `dev_` prefix.

---

## The UI and IAM

### 9. What can you actually do in the Composer UI, and what are the two places people get stuck?

**The Composer UI is the Airflow UI.** There is no separate console. You get the full Airflow 2.x interface: DAG list, grid view, graph view, calendar, task instance views, logs, XCom, connections, variables, config, and the backfill dialog.

The two places people get stuck:

1. **The Grid view vs the Graph view.** Grid is a matrix of runs × tasks, coloured by state — it is the right view for "which day did this break?" Graph is the node diagram for a *single* run — it is the right view for "what is this DAG's shape?" People open Grid expecting a graph, see coloured squares, and conclude the UI is broken.
2. **The XCom tab.** It shows what a task pushed, which is invaluable for a "why is my downstream task not seeing the data" question — and dangerous, because it shows values you might not want visible, and it shows them from the metadata DB, so it is a place where a leaked payload stays.

Also worth knowing: the UI shows the **import error** for a DAG file that failed to parse, which is the fastest way to diagnose "my DAG is not in the list".

**The failure story:** a team spent a day debugging a DAG that "wasn't running" because they were looking at the Graph view of a *different logical date* than the one that failed. The Grid view showed a red cell on 2026-01-14; the Graph view they had open was 2026-01-15, which was green. The lesson: **Grid first to find which run is broken, Graph second to understand why.**

### 10. How does Composer handle access control, and how should IAM be split across teams?

**Composer 2.x uses IAM-based access control instead of Airflow's own RBAC** (Composer 3 adds the built-in RBAC back as a built-in feature). This has a direct operational consequence: **there is no in-Airflow permission boundary between teams** unless you use Composer 3's RBAC or separate environments.

So IAM is the boundary, and it is layered:

| Role | Grants |
|---|---|
| `roles/composer.user` | view the UI, browse DAGs, view logs |
| `roles/composer.worker` | run tasks against GCP resources in the environment's project |
| `roles/composer.admin` | edit the environment, change config, delete it |
| The environment's **service agent** | the identity the *environment* runs as; it needs BigQuery/GCS/Dataflow access |

The design principle: **the service account's permissions are the environment's real blast radius.** If the Composer service agent has project-wide `roles/bigquery.dataEditor`, then every DAG in the environment — including a team's experimental one — can write to every table in the project.

The narrower pattern:

- Give the environment's service agent access only to the datasets and buckets the environment needs.
- Keep per-team write access in the individual **Connections** rather than in the environment-wide identity.
- Never put a service-account key in the DAG bundle; use the attached identity.
- Split `composer.admin` from `composer.user` — the admin role can change the environment's config and delete it.

**The failure story:** a data-science team uploaded an experimental DAG that wrote to `analytics.revenue_enriched` "just to test". The Composer service agent had project-wide BigQuery data-editor access, granted early on for convenience. The experimental DAG used `WRITE_TRUNCATE` with no partition decorator and truncated the production revenue table. The nightly pipeline then reloaded one day into an otherwise empty table. Recovery took 5 hours and a full 90-day rebuild from raw. The fix was per-dataset IAM for the environment service agent, and a structure test asserting every `BigQueryInsertJobOperator` has a partition decorator.

### 11. What is the difference between the Composer-managed Cloud SQL instance and one you supply, and why does it matter for cost and for cleanup?

**Composer creates and manages a Cloud SQL for Postgres instance for the metadata database by default. You can instead supply your own instance**, which changes three things: cost attribution, lifecycle, and the blast radius of a metadata-DB problem.

| | Composer-managed Cloud SQL | Customer-managed Cloud SQL |
|---|---|---|
| Lifecycle | created and deleted with the environment | **yours** — survives environment deletion |
| Version control | you cannot upgrade the Airflow/Postgres combination independently | you control the Postgres version |
| Cost | bundled into the environment estimate | billed separately, in your Cloud SQL budget |
| Access | only Composer touches it | you can connect, back up, tune, and read it |
| Multi-environment | one per environment | several environments can share one (with caveats) |

The last row in the middle is the operational win: **with your own instance you can read the metadata DB directly.** That means you can query `dag_run` and `task_instance` for reporting, SLA computation, and audit — which is exactly what you need to build the compliance metric the course's `sla_tracker.py` describes.

**The failure story:** a team wanted to compute SLA compliance over 6 months, and the compliance numbers were wrong because backfill runs were counted as fresh misses. The fix was to exclude `run_type='backfill'` runs — but they could not write the query, because the metadata DB was Composer-managed and not network-accessible from their reporting project. They had to export the results from the UI one run at a time. With a customer-managed instance this is a one-line SQL query against `dag_run`.

---

## Composer vs self-managed Airflow

### 12. Composer or self-managed Airflow? Give the decision, and say when Composer is the wrong answer.

**Composer is the right answer unless you have a specific requirement it cannot meet.** The comparison:

| | Self-managed Airflow on Kubernetes | Cloud Composer |
|---|---|---|
| Who runs the cluster | you | Google |
| Who runs the scheduler, workers, web server, broker | you | Google |
| Metadata DB | you | Cloud SQL (managed or yours) |
| DAG storage | wherever you like | GCS bucket |
| 30–60 s pod startup | yes, with `KubernetesExecutor` | **no** — Composer's workers are long-lived |
| Per-task resource profiles | yes | only with the KubernetesExecutor |
| Per-task images | yes | via `KubernetesPodOperator` referencing your registry |
| Custom networking / VPC-SC | yes | constrained |
| Airflow version choice | yours | pinned by the image version, upgradeable |
| Cost | cluster + ops | per-environment, mostly fixed |

**Composer wins on:** time to first DAG (minutes, not days), no cluster to operate, autoscaling workers, IAM-native access control, environment versioning for safe Airflow upgrades, and Google Cloud integrations (BigQuery, GCS, Dataproc, Dataflow, GKE, Cloud Run).

**Self-managed wins on:** requirements Composer cannot satisfy — a specific Airflow version or a provider that Composer has not packaged, unusual networking (private ranges Composer cannot use, VPC-SC constraints), a per-task resource shape Composer does not offer, or full control of the metadata DB and the DAG storage.

**The pragmatic recommendation:** *if you are on Google Cloud and your tasks are ordinary — queries, API calls, moderate Python — use Composer with the default executor.* The KubernetesExecutor's benefits (per-task resources, per-task images) are real but usually not worth the startup tax at typical task durations. Choose it only when you genuinely need per-task resources or images, and accept the ~45-second cost knowingly.

**The failure story:** a team moved 60 DAGs to Composer and hit two problems they had not anticipated. First, one DAG used an Airflow provider that Composer had not packaged — it needed a custom image, and Composer's DAG distribution model does not let you ship a custom provider image per DAG. They had to fork the provider or move that DAG to a second self-managed environment. Second, a compliance requirement mandated the metadata DB live in a specific region with a specific encryption key (CMEK), and the Composer-managed instance could not be configured with CMEK. Both problems were discovered *after* the migration. The lesson: **check the two or three hard requirements (provider availability, network placement, encryption) before you migrate, not after.**

---

## Next module

→ [Top 50 — the night-before revision](top-50.md)

---

## Related chapters

| Module section | Chapter |
|---|---|
| Composer's shape, versions, IAM (1–6, 9–11) | [02-airflow-architecture-and-concepts](../chapters/02-airflow-architecture-and-concepts.md) |
| Executors and workers, environment sizing (7) | [10-executors-and-workers](../chapters/10-executors-and-workers.md) |
| KubernetesExecutor vs Composer (8, 12) | [16-airflow-on-kubernetes](../chapters/16-airflow-on-kubernetes.md) |
| Cost, BigQuery scheduled queries, decision procedure (11–12) | [15-airflow-vs-beam-vs-spark](../chapters/15-airflow-vs-beam-vs-spark.md) |
| Cleaning up / deletion (3–5) | [03-dags-and-scheduling](../chapters/03-dags-and-scheduling.md) |
