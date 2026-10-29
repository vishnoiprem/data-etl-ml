# 4.10 — Executors & Workers

> **Section 4 · Advanced Orchestration · Lecture 4.10 · 7:30**

## 🎯 What you will learn

- What an executor actually does: it is a **queue**, not a worker
- The five executors Airflow ships, and the one Airflow 2.x removed
- How Composer maps your DAGs onto managed infrastructure — and why you mostly do not get to choose
- `CeleryExecutor` caveats: the broker, Flower, and what breaks when the broker is unreachable
- `KubernetesExecutor`: pod templates, RBAC, namespaces, and the 30–60s pod startup tax
- Why worker lifetime is a cost decision, and how short-lived workers change your design
- How to pick: a decision table, and the two questions that decide it

---

## 🧠 Concept

### The executor is a queue, not a worker

This is the conceptual point that makes everything else fall into place.

Airflow's runtime has three moving parts:

```text
┌────────────────┐    writes     ┌──────────────────┐    picks up    ┌──────────────┐
│   Scheduler    │──────────────▶│  Executor queue │◀──────────────│   Worker     │
│                │   task to run │  (the broker)   │   task to run │  (runs the  │
│  decides *what*│               │                  │               │   callable)  │
│  should run    │               │  decides *where* │               │  decides     │
│                │               │   it runs        │               │   the answer │
└────────────────┘               └──────────────────┘               └──────────────┘
```

- The **scheduler** decides *what* should run. It reads the DAG definitions, evaluates the dependency graph, checks the trigger rules, and asks the executor to run a task instance.
- The **executor** is the **queue** between them. It is a transport mechanism: "here is a command, give it to a worker, tell me when it is done".
- The **worker** actually runs the task's callable. It pulls from the queue, executes, and reports the result back to the scheduler (via the metadata database).

The executor name tells you *what kind of queue* is in the middle.

| Executor | The queue is… | A task runs… |
|---|---|---|
| `SequentialExecutor` | a single in-process slot | in the scheduler process itself |
| `LocalExecutor` | a local `multiprocessing` pool | in a subprocess of the scheduler |
| `CeleryExecutor` | a message broker (Redis/RabbitMQ) | in a Celery worker process |
| `KubernetesExecutor` | the Kubernetes API server | in a brand-new pod |
| `DaskExecutor` | a Dask cluster's scheduler | in a Dask worker |
| `LocalExecutor` (Airflow 3) | — | — |

**`SequentialExecutor`** ran one task at a time, inside the scheduler process itself. It existed so the DAG-authoring API had *something* to fall back on when no better executor was configured; it was never for production, and it was **removed in Airflow 2.0**. If you find it in old code, that code predates 2.0.

**`LocalExecutor`** spawns a Python subprocess per task, from a pool controlled by the `parallelism` setting. It needs no external infrastructure, which makes it the default for `airflow standalone` and for a laptop. It is a genuine production option for a small, single-machine Airflow — a small team running a dozen light DAGs on one VM will happily use it.

**`CeleryExecutor`** puts a real message broker in the middle. The scheduler publishes a command; any Celery worker can pick it up. This gives you a genuinely distributed pool of workers, and it is the standard self-managed choice.

**`KubernetesExecutor`** replaces the broker with the Kubernetes API. The scheduler creates a Pod to run each task; the Pod executes and then exits. There is no long-lived worker pool at all.

**`DaskExecutor`** distributes tasks onto a Dask cluster. It exists mainly for people who already run Dask.

### Worker lifetime: the cost axis that decides everything

The executors differ on one axis that matters more than throughput: **how long does a worker live, and what does it cost while it lives?**

```text
SequentialExecutor:   scheduler process ── one task at a time, forever
LocalExecutor:       N subprocesses, forked per task, reaped at the end
CeleryExecutor:      M long-lived workers, reused across every task
KubernetesExecutor:  one Pod per task, created and destroyed
```

| | Local | Celery | Kubernetes |
|---|---|---|---|
| Worker startup cost | ~milliseconds (fork) | ~seconds (worker already up) | **~30–60 seconds** (pull image, schedule, mount volumes) |
| Idle cost | low (subprocesses exit) | **billed for the whole worker lifetime** | zero (no pod, no cost) |
| Isolation | process | process | **container + namespace + security context** |
| Scaling | limited by the machine | add workers, add cost | add replicas, add cost only while busy |
| Heterogeneous resources | no | no | **yes — a different pod template per task** |

The trade is stark: **long-lived workers are cheap to start and expensive to idle; short-lived workers are free to idle and expensive to start.** A task that takes 5 seconds and a pod that takes 45 seconds to start is a terrible trade. A task that takes 45 minutes is a great one.

### How Composer maps to executors

Cloud Composer is a managed Airflow. You do not pick the executor for the *default* Composer environment in the usual sense — but you should know what is underneath, because it explains the behaviour you see.

| Composer environment | Executor | Notes |
|---|---|---|
| Composer 1 (Airflow 1.x/2.x) | `CeleryExecutor` | Managed Celery workers + a managed broker. You size the worker pool. |
| Composer 2 (Airflow 2.x) | `CeleryExecutor` (default) or `KubernetesExecutor` | You can choose the executor when you create the environment. |
| Composer 3 (Airflow 2.x, newer) | `CeleryExecutor` | With pre-installed Airflow 2.x and managed infra. |

The important consequence: **on Composer, a task's compute runs in a worker that Composer manages, and the environment's worker pool size is a cost knob you control.**

Two Composer-specific behaviours worth internalising:

**1. The scheduler is a singleton.** One scheduler process decides what runs. It is a single point of failure for *scheduling*, but not for *running* — already-running tasks continue. This is why the Composer SLA guarantees a scheduler, and why a brief scheduler restart does not fail your DAGs.

**2. Worker sizing is per-environment, not per-DAG.** You give the environment a worker pool; every DAG in it shares it. A DAG with 50 concurrent sensors can starve a DAG with 3 tasks. Chapter 9's "sensors are expensive" is a Composer-level problem for exactly this reason.

### `CeleryExecutor` caveats

Celery is the default, so its failure modes are the ones you will actually hit.

**The broker.** Celery needs a message broker: Redis or RabbitMQ. The scheduler publishes task commands to a queue; workers consume them; results go back through the broker (or a result backend).

The broker is a **single point of failure** that is not the database. If the broker is unreachable, the scheduler cannot hand out work, and the database looks perfectly healthy while nothing runs.

```text
OperationalError: Could not connect to the broker
```

This is the canonical Celery-in-Airflow error. It means the Airflow worker (or the scheduler) could not open a connection to the broker at the configured URL. Common causes:

| Cause | How to spot it |
|---|---|
| Broker is down or restarting | `redis-cli ping` / `nc -z broker-host 5672` fails |
| Wrong broker URL | The URL in the Airflow config does not match the deployed broker |
| Credentials / network policy | Connection times out rather than refusing |
| TLS misconfiguration | `ssl.CAErrors` / certificate verification errors |

In a self-managed Airflow, the fix is to fix the broker. In Composer, the broker is managed — but the same error appears if your environment's networking or VPC-SC configuration is wrong.

**Flower.** Flower is Celery's monitoring web UI. On a self-managed Celery Airflow, Flower is how you see which worker picked up which task, how long the queue is, and whether workers are alive.

```bash
airflow celery flower --port 5555
```

In Composer, Flower is not exposed to you directly — Composer provides its own monitoring instead. This is a real operational difference: **on self-managed Celery Airflow, Flower is your primary debugging tool for "why isn't my task running"; on Composer it is not available to you.**

**Other Celery caveats worth knowing:**

- **Task distribution.** Celery workers can execute tasks out of dependency order relative to your mental model, but Airflow's scheduler still enforces dependencies. A task is only *queued* when its upstream tasks are done.
- **Result backend size.** A task that returns 10 MB lands in the result backend. Airflow's XCom has a size limit (48 KB by default in Airflow 2.x); the Celery result backend has its own. Large returns cause confusing failures.
- **Worker pre-emption.** On spot/preemptible workers, a pre-empted task is lost and retried. Celery's visibility timeout must exceed the longest task, or a task can be delivered twice.

### `KubernetesExecutor`

The KubernetesExecutor inverts the model. Instead of "send the task to a worker", it says "create a Pod to run this task".

```text
Scheduler ──▶ Kubernetes API ──▶ create Pod ──▶ Pod runs the task ──▶ Pod exits
                                            ◀── watch Pod status ─────┘
```

**Pod templates.** The executor needs to know how to build a Pod. That is what a `pod_template_file` is — a YAML file with the Pod spec.

```yaml
# kubernetes_pod_template.yaml
apiVersion: v1
kind: Pod
metadata:
  name: dummy-name
  labels:
    app: airflow
spec:
  restartPolicy: Never
  serviceAccountName: airflow-worker
  containers:
    - name: base
      image: gcr.io/my-project/airflow:2.9.3
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
      volumeMounts:
        - name: airflow-logs
          mountPath: /opt/airflow/logs
  volumes:
    - name: airflow-logs
      persistentVolumeClaim:
        claimName: airflow-logs
```

The executor fills in the Pod name, the command, the arguments, the environment, and the volumes. You supply the shape.

**A pod template per task.** The power of the KubernetesExecutor is that different tasks can use different templates — a Spark task wants 8 CPUs and 32 GB, a sensor wants almost nothing. You point `pod_template_file` at a different YAML per task.

**RBAC.** The scheduler's service account needs permission to create, watch, and delete Pods in the namespace where tasks run.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: airflow-pod-creator
  namespace: airflow
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["create", "get", "list", "watch", "delete"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get", "list"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "get", "list", "watch", "delete"]
```

If the binding is missing or wrong, the scheduler's attempt to create the Pod fails:

```text
Pod creation failed: 403 Forbidden
```

or, from the Kubernetes API directly:

```text
pods "airflow-task-20260115-0001" is forbidden: User "system:serviceaccount:airflow:airflow-scheduler" cannot create resource "pods" in API group "" in the namespace "airflow"
```

That is the canonical KubernetesExecutor permission error, and it is always an RBAC problem, not a code problem.

**Namespaces.** Tasks can run in a different namespace from the scheduler, which is how you isolate a noisy tenant or pin a task to a specific node pool. The scheduler's `Role` must then be a `ClusterRole` (or a `Role` in each target namespace) bound appropriately.

**The startup tax.** This is the number that decides whether the KubernetesExecutor is viable for your workload:

> **A Kubernetes Pod takes roughly 30–60 seconds to start:** the scheduler must find a node, the kubelet must pull and unpack the image, the container must start, the Airflow command must be launched, and the task must report in.

Add that to every task. A DAG of 20 tasks, all of which can run in parallel, still takes ~45 seconds before the *first* byte of work happens. A DAG of 20 *sequential* tasks pays 20 × 45 seconds = **15 minutes of pure startup**.

| Task runtime | Startup overhead | Effective efficiency |
|---|---|---|
| 5 seconds | 45s | ~10% |
| 1 minute | 45s | ~57% |
| 5 minutes | 45s | ~87% |
| 45 minutes | 45s | ~98% |

**The rule: the KubernetesExecutor is good for heavy tasks and terrible for chatty ones.** If your DAG has a hundred tasks that each take three seconds, do not put it on Kubernetes.

### How to pick

Two questions decide it:

1. **How long does a typical task run?** Under a minute → long-lived workers (Celery). Over a few minutes → either works; measure.
2. **Do the tasks need heterogeneous resources or isolation?** Yes → Kubernetes.

| Situation | Executor | Why |
|---|---|---|
| A laptop, learning, CI | `LocalExecutor` | No infrastructure to operate |
| Small single-VM production Airflow, light DAGs | `LocalExecutor` | No broker to run |
| Distributed workers, uniform task sizes | `CeleryExecutor` | Low startup cost, mature ecosystem |
| Heavy tasks, varied resource needs, strong isolation | `KubernetesExecutor` | One Pod per task, per-task resources |
| You already run Dask | `DaskExecutor` | One cluster to operate |
| Managed Airflow (Composer) | Composer manages it | You size the environment, not the executor |

**On Composer specifically**, the practical decision is not "which executor" but "how many workers, and how big". A Composer environment's worker count and machine type are its cost knobs, and chapter 15's cost section comes back to this.

### The queue, restated

One more piece of vocabulary, because "executor" and "queue" get used interchangeably and it matters when you are debugging:

| Term | Means | In Airflow |
|---|---|---|
| **Queue** | Where task commands wait | The broker (Celery) or the K8s API (KubernetesExecutor) |
| **Executor** | The component that manages the queue | The `BaseExecutor` subclass |
| **Worker** | The thing that runs a task | A Celery worker process, a Pod, a forked subprocess |
| **Concurrency** | How many tasks may run at once | `parallelism`, `max_active_tasks_per_dag`, `max_active_runs` |
| **Pool** | The set of workers | The Celery worker fleet, or the K8s node pool |

When someone says "the queue is backed up", they mean task commands are waiting for a free worker — not that the scheduler is confused, and not that the database is slow. Those are three different problems with three different dashboards.

---

## 🛠️ Hands-On

### Step 1 — read the course DAGs and identify the execution model

```bash
cd data-engineering/data-Course/google/composer
ls project/dags/
```

```text
01_hello_world.py
02_templating_and_variables.py
03_etl_bigquery.py
04_branching_and_xcom.py
dag_config.py
```

None of these import an executor — that is correct. The executor is a deployment concern, configured in `airflow.cfg` (or in Composer's environment configuration), not in a DAG file.

Confirm that by checking the local runner, which models the *scheduler* side of the picture:

```bash
grep -n "class DAG" -A 30 project/local_runner.py | head -40
```

The `DAG` class holds `tasks`, `schedule`, `start_date`, `catchup`, `max_active_runs`, and `description` — exactly the scheduling concepts. It has no executor and no worker concept, because the local runner *is* both: it schedules and runs tasks in-process.

### Step 2 — model the queue explicitly, with the real course DAGs

The local runner's `run_dag` function is a topological walk. That walk *is* the scheduler's job. Let us extract it into a shape you can reason about — a queue of ready tasks, drained by a pool of workers.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project")
sys.path.insert(0, "project/core")

from local_runner import DAGS, _dependency_order

# The scheduler's view of the DAG: which tasks are ready to be queued?
for name in ("etl_to_gcs", "branching_load", "xcom_pipeline", "templating_paths"):
    dag = DAGS[name]()
    ready = [
        t for t, task in dag.tasks.items()
        if not task.dependencies
    ]
    print(f"{name:<18} tasks={len(dag.tasks):<3} immediately-ready={ready}")
PY
```

Expected output:

```text
etl_to_gcs         tasks=4   immediately-ready=['read_orders']
branching_load     tasks=6   immediately-ready=['read_orders']
xcom_pipeline      tasks=5   immediately-ready=['read_orders']
templating_paths   tasks=4   immediately-ready=['read_orders']
```

Every DAG in the course starts with exactly one ready task, so every DAG is a chain — no fan-out, no concurrency, no queueing. That is a useful thing to know: **the course's DAGs would take exactly as long on a `SequentialExecutor` as on a 100-worker `CeleryExecutor`**, because there is never more than one task ready at a time.

### Step 3 — build a DAG with real fan-out and measure the difference

Fan-out is where executors matter. Let us build one, using the course's real functions.

```python
# project/core/fanout.py
"""Fan-out helpers: split work by region so the DAG can parallelise."""
from __future__ import annotations

from pipeline_logic import summarise_by_region


def regions_to_process(summary: dict[str, dict[str, float]]) -> list[str]:
    """Return the regions that produced revenue, sorted.

    A fan-out task returns this list, and a dynamically-mapped task
    turns it into one task instance per region.

    Args:
        summary: The output of `summarise_by_region`.

    Returns:
        A sorted list of region codes.
    """
    return sorted(
        region for region, bucket in summary.items() if bucket["order_count"] > 0
    )


def region_summary_csv(summary: dict[str, dict[str, float]], region: str) -> str:
    """Render the summary for a single region.

    Args:
        summary: The output of `summarise_by_region`.
        region: The region to render.

    Returns:
        A CSV document with a header and one data row.
    """
    bucket = summary[region]
    return (
        "region,order_count,revenue_eur\n"
        f"{region},{int(bucket['order_count'])},{bucket['revenue_eur']:.2f}\n"
    )
```

Now run it against the real sample data:

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region
from fanout import regions_to_process, region_summary_csv

lines = open("sample_data/orders.csv").read().splitlines()
accepted, _ = transform_orders(lines)
summary = summarise_by_region(accepted)

regions = regions_to_process(summary)
print(f"regions to process: {regions}  (count={len(regions)})")
for region in regions:
    print(region_summary_csv(summary, region), end="")
PY
```

Expected output:

```text
regions to process: ['AMER', 'APAC', 'EMEA', 'LATAM']  (count=4)
region,order_count,revenue_eur
AMER,318,113592.19
region,order_count,revenue_eur
APAC,285,108194.92
region,order_count,revenue_eur
EMEA,322,118423.22
region,order_count,revenue_eur
LATAM,320,110646.18
```

Four regions → four task instances under dynamic task mapping (chapter 14). With one worker, that is 4 × 45s = 180 seconds of pod startup (Kubernetes) or 4 × 2s = 8 seconds of Celery reuse.

### Step 4 — model the Kubernetes startup tax concretely

```bash
python3 - <<'PY'
# What does the executor choice cost for a fan-out of 4 regions?
TASKS = 4
POD_STARTUP = 45      # seconds, typical Kubernetes Pod start
CELERY_STARTUP = 0.5   # seconds, worker already running and reused
TASK_WORK = 30         # seconds of real work per task

print("executor          startup total   wall time (parallel workers)   vs sequential")
print("-" * 82)
for name, startup, workers in (
    ("Celery (1 worker)", CELERY_STARTUP, 1),
    ("Celery (4 workers)", CELERY_STARTUP, 4),
    ("Kubernetes (1 pod/task)", POD_STARTUP, TASKS),
):
    sequential = TASKS * (startup + TASK_WORK)
    parallel = startup + TASKS * (startup + TASK_WORK) / workers
    print(f"{name:<19} {TASKS * startup:>8.0f}s      {parallel:>12.0f}s              {sequential:>8.0f}s")
PY
```

Expected output:

```text
executor          startup total   wall time (parallel workers)   vs sequential
----------------------------------------------------------------------------------
Celery (1 worker)          2s               122s                   122s
Celery (4 workers)         2s                31s                   122s
Kubernetes (1 pod/task)      180s               120s                   300s
```

The Kubernetes row is the whole story in three numbers. It finishes in 120 seconds of wall time — a hair faster than the single-worker Celery run (122s) — but it burned **180 seconds of pod startup** to get there, and the sequential comparison (300s) shows what it would cost if the tasks could not run in parallel. Note the arithmetic: `45 + 4 × (45 + 30) / 4 = 120s`. The four Pods start together, so the startup tax is paid **once in wall-clock terms**, not four times — but it is still four Pods' worth of real cluster capacity.

The four-worker Celery row is faster still (31s), because a warm worker starts work immediately and the Pod tax never applies. **The executor decision is not "which is faster" — it is "what does a task need."** When the four tasks need different images, different memory limits, or different node types, the four-worker Celery option does not exist.

### Step 5 — read the executor-relevant settings from the course's `dag_config.py`

```bash
grep -n "SLA\|RETRIES\|SCHEDULE" project/dags/dag_config.py
```

Expected output:

```text
65:SCHEDULE = "@daily"
68:#: Airflow's SLA is measured against the *data interval end*, not the
70:DEFAULT_SLA = dt.timedelta(hours=2)
73:DEFAULT_RETRIES = 2
```

Note the line numbers — `grep -n` gives them, so you can jump straight to the setting. The `DEFAULT_RETRY_DELAY` line is not in the output because the pattern matches `RETRIES` but not `RETRY_DELAY`; widen the pattern if you want it.

`DEFAULT_SLA = 2 hours` is the number that interacts with the executor. If each task costs 45 seconds of Kubernetes startup and the DAG has 20 sequential tasks, the DAG consumes 15 minutes of pure startup — 12.5% of its entire SLA budget, spent doing nothing.

---

## 🛠️ Common Errors and Fixes

### `OperationalError: Could not connect to the broker`

The Celery worker or the scheduler could not reach the message broker.

**Cause:** the broker is down, the broker URL is wrong, or the network path is blocked.

**Fix:**
```bash
# Is the broker up?
redis-cli -h YOUR_BROKER_HOST ping
# Expected: PONG

# Can we reach the port at all?
nc -z YOUR_BROKER_HOST 6379
# Expected: connection succeeded

# What does Airflow think the broker URL is?
airflow config get-value celery broker_url
```

If the broker is fine and the URL is right, the problem is network-level: a firewall rule, a security group, or a VPC-SC perimeter. On Composer, check that the environment's VPC-SC configuration still permits the broker and the metadata server.

### `Pod creation failed: 403 Forbidden`

The KubernetesExecutor could not create the task's Pod.

**Cause:** the scheduler's service account lacks `create` on `pods` in the target namespace.

**Fix:** grant the permission and bind the role to the service account.

```bash
kubectl create rolebinding airflow-pod-creator \
  --clusterrole=airflow-pod-creator \
  --serviceaccount=airflow:airflow-scheduler \
  --namespace=airflow
```

Then verify the exact error the API returned:

```bash
kubectl auth can-i create pods --as=system:serviceaccount:airflow:airflow-scheduler -n airflow
# Expected: yes
```

If this says `no`, the problem is RBAC. If it says `yes` and the task still fails, look at the Pod's own admission (quotas, node selectors, image pull secrets).

### `Max number of active tasks allowed (16) reached`

The DAG's `max_active_tasks_per_dag` limit was hit.

**Cause:** too many tasks queued at once — usually sensors (chapter 9) or a dynamic task mapping with too many instances.

**Fix:**
- Reduce the fan-out width, or batch the work.
- Raise `max_active_tasks_per_dag` **only after** confirming the environment has spare worker capacity. On Composer, raising this without adding workers just moves the queue from Airflow to the broker.
- Check whether the tasks are actually running or just queued — the two look identical in the UI.

### `airflow.exceptions.DagNotFound: DAG: [my_dag] not found`

**Cause:** the referenced DAG is not in the environment. On the KubernetesExecutor, a common variant is that the DAG file imported but failed during parse, so the scheduler never registered it — the file is in the bucket but the DAG is not in the list.

**Fix:** check the DAG list in the Composer UI, then check the DAG import errors in the environment's logs. A syntax error or a missing provider package shows up there, not in the task log.

### The task never starts; the queue is full and the workers are idle

**Cause:** a mismatch between what the scheduler thinks the concurrency is and what the worker pool can actually run.

**Fix:** check all four numbers, because they are separate settings:

| Setting | Scope | Controls |
|---|---|---|
| `parallelism` | environment | Total concurrent task instances |
| `max_active_tasks_per_dag` | DAG | Concurrent tasks in one DAG run |
| `max_active_runs` | DAG | Concurrent *runs* of the DAG |
| Worker count | environment | How many tasks can actually execute |

If `parallelism=16` but the environment has 4 workers, 12 task instances sit in the queue. They are not running and they are not failed; they are *queued*.

### The task fails with `Pod creation failed: 0/3 nodes available`

**Cause:** the cluster cannot satisfy the Pod's scheduling constraints — not enough nodes with the requested resources, a node selector matching nothing, or a taint the Pod does not tolerate.

**Fix:** relax the resource requests, fix the node selector, or add capacity. In a managed Composer environment, the equivalent symptom is a task that stays `scheduled` for a long time before starting.

### `403 Forbidden` on an image pull

**Cause:** the Pod cannot pull its image — no image pull secret in the namespace, or the service account lacks `get` on the secret.

**Fix:**
```bash
kubectl create secret docker-registry regcred \
  --docker-server=YOUR_REGISTRY \
  --docker-username=YOUR_USER \
  --docker-password=YOUR_TOKEN \
  --namespace=airflow
```
And reference it in the pod template:
```yaml
spec:
  imagePullSecrets:
    - name: regcred
```

### The task is executed twice

**Cause:** on Celery with pre-emptible workers, or on Kubernetes with a Pod that is evicted mid-run, the task can be delivered twice.

**Fix:** make the task idempotent (chapter 12). This is not really fixable at the executor level — at-least-once execution is the model's promise, and the only correct response is idempotent tasks.

---

## 💡 Production Notes

- **The executor is the queue; the worker is the thing that runs the code.** When you debug "why is my task not running", check the queue first and the worker second.
- **On Composer you size the environment, not the executor.** Worker count and machine type are your cost and throughput knobs.
- **Measure the real task duration before choosing Kubernetes.** If the median task is under a minute, the 30–60s pod startup will dominate. A useful rule: the startup overhead is acceptable when `task_duration > 10 × startup`.
- **Celery's broker is a separate failure domain from the database.** `OperationalError: Could not connect to the broker` with a healthy database is a normal, expected state of a misconfigured Celery Airflow.
- **Flower is your Celery debugging tool and Composer does not expose it.** On self-managed Airflow, learn to read Flower; on Composer, use the Cloud Monitoring metrics instead.
- **Prefer a homogeneous worker pool unless you truly need per-task resources.** Heterogeneous pod templates are powerful and operationally expensive: more images to maintain, more RBAC to get right, more ways to fail.
- **Concurrency limits are not throughput settings.** Raising `parallelism` without adding workers turns running tasks into queued tasks. Raise the pool or lower the demand.
- **Short-lived workers make idempotency non-negotiable.** With per-task pods, a pod can be evicted mid-task and the task re-run. Chapter 12 is not optional.
- **Watch `max_active_runs`.** A DAG with `max_active_runs=1` and a 2-hour SLA is serialising runs; with `catchup=True` it will build a backlog that takes days to drain.
- **On Composer, the scheduler is a singleton.** A scheduler restart does not fail running tasks, but it does pause *scheduling* — which matters for time-critical DAGs.

---

## 🔑 Key Takeaways

- **The executor is the queue; the worker runs the task.** The scheduler decides *what*, the executor decides *where*.
- `LocalExecutor` forks subprocesses (no infrastructure); `CeleryExecutor` uses a broker and a long-lived worker fleet; `KubernetesExecutor` creates one Pod per task; `DaskExecutor` spreads onto a Dask cluster. `SequentialExecutor` was removed in Airflow 2.0.
- **Long-lived workers: cheap to start, expensive to idle. Short-lived workers: free to idle, expensive to start.** That is the axis on which the executors differ.
- Composer 2 runs `CeleryExecutor` by default (you can choose `KubernetesExecutor` when creating the environment); Composer 1 was Celery-only.
- **Celery caveats:** a broker that is a separate failure domain (`OperationalError: Could not connect to the broker`), and Flower for monitoring — which Composer does not expose.
- **KubernetesExecutor caveats:** pod templates per task, RBAC on the scheduler's service account (`403 Forbidden` otherwise), namespaces for isolation, and a **30–60 second startup tax** on every task.
- The startup tax is acceptable when `task_duration > 10 × startup`. Below that, use long-lived workers.
- **To pick:** long task + heterogeneous resources → Kubernetes. Short tasks, uniform, many → Celery. One machine, light → Local.
- **Four separate limits** — `parallelism`, `max_active_tasks_per_dag`, `max_active_runs`, worker count — and a task can be queued in all four senses at once.

---

## 📚 Practice Exercises

1. **Measure the real task duration.** Instrument the course's `etl_to_gcs` DAG to record how long each task takes, and compute the median. Then decide whether it could run on the KubernetesExecutor within a 2-hour SLA if the DAG had 50 sequential tasks. *Expected answer:* the median task in the course project is a few seconds, because the dataset is 5,000 rows. 50 tasks × (45s startup + ~2s work) ≈ 39 minutes of wall time and ~37 minutes of pure startup — 31% of the 2-hour SLA consumed by pod creation. The conclusion is that the course's DAG shape is a bad KubernetesExecutor fit unless the tasks are made much heavier.

2. **Build a fan-out DAG and a fan-in DAG.** Use `regions_to_process` and `region_summary_csv` from `core/fanout.py` to build a DAG that processes each of the four regions in parallel and then joins. Write the Airflow 2.5+ dynamic task mapping code. Then explain what happens to the four mapped task instances when one of them fails, and what trigger rule the join task needs. *Expected answer:* with `.expand(region=regions)`, four task instances are created; if one fails, the join task with the default `all_success` trigger rule is marked `upstream_failed` and does not run; the join task needs `trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS` (or `all_done`) to run even though one mapped instance failed.

3. **Diagnose a stuck queue.** A Composer environment has 8 workers. A DAG has `max_active_tasks_per_dag=16`, `max_active_runs=2`, and 10 sensors in `mode="reschedule"`, each with `timeout=3600` and `poke_interval=300`. The DAG shows 16 tasks in `running`, nothing in the UI is making progress, and the worker utilisation graph is flat at 8. Explain what is happening, in terms of the four limits from this chapter, and propose two fixes. *Expected answer:* the 16 sensors fill the DAG's per-DAG concurrency limit of 16; they are all in `running` state, so they consume 16 of the environment's 8-worker pool; only 8 are executing checks at a time and the rest are reschedule-queued; the `max_active_runs=2` allows a second run to double the contention. Fix 1: convert the sensors to deferrable operators, which leave the running state entirely. Fix 2: consolidate the 10 sensors into one sensor that checks all 10 conditions.

4. **Write a pod template and the RBAC to go with it.** Write a Kubernetes pod template for a task that runs a PySpark job needing 4 vCPU and 16 GB, plus the Role and RoleBinding that let the scheduler create it in the `airflow` namespace. Then state the exact error Airflow raises if the RoleBinding is missing, and the exact error if the namespace is wrong. *Expected answer:* missing binding → `Pod creation failed: 403 Forbidden` (or the API's `pods "..." is forbidden: User "system:serviceaccount:airflow:airflow-scheduler" cannot create resource "pods" ... in the namespace "airflow"`); wrong namespace → the same 403, but the error names the namespace that was actually used, which is the clue.

5. **Compare the cost of two executor strategies.** A DAG has 100 tasks, each doing 20 seconds of work. Strategy A runs on 8 long-lived Celery workers (workers already running). Strategy B runs on the KubernetesExecutor with one Pod per task, 8 Pods at a time. Compute the wall time and the "compute-seconds" (wall time × workers) for each, plus the total pod-startup seconds. *Expected answer:* Celery — each task costs 20.5s (0.5s dispatch + 20s work); 100 tasks / 8 workers ≈ 13 rounds × 20.5s ≈ 266s wall time, ≈ 2,128 compute-seconds, and zero startup beyond the initial dispatch. Kubernetes — each task costs 65s (45s startup + 20s work); 100 tasks / 8 parallel pods ≈ 13 rounds × 65s ≈ 845s wall time, ≈ 6,760 compute-seconds, and 4,500 total pod-startup seconds. Kubernetes is ~3.2× slower in wall time and ~3.2× more expensive in compute-seconds for this workload. Conclusion: the KubernetesExecutor is the wrong choice here; it becomes right only if the task work grows past a few minutes.

6. **Explain the queue to a colleague.** Describe, in under 200 words and without using the word "executor", the difference between these four states: (a) a task that is waiting for an upstream task, (b) a task that is queued but no worker is free, (c) a task that is running, and (d) a task that has been deferred by a deferrable operator. Then say which one shows up in the `Max number of active tasks allowed (16) reached` error. *Expected answer:* (a) is `upstream_failed`/`upstream_failed`-adjacent or simply not scheduled — it is blocked by the dependency graph and consumes no queue slot; (b) it is `scheduled` and waiting for a worker, consuming a concurrency slot but no worker; (c) it is `running` and holds a worker; (d) it is `deferred` and holds neither a worker nor a concurrency slot, waiting on a triggerer. The "Max number of active tasks allowed" error refers to (b) and (c) together — running *and* scheduled task instances both count toward the limit.

---

## 📖 Further Reading

- Airflow executors overview — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html
- Airflow CeleryExecutor — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/celery.html
- Airflow KubernetesExecutor — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html
- Airflow LocalExecutor — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/local.html
- Airflow DaskExecutor — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/dask.html
- Airflow configuration reference (`parallelism`, `max_active_tasks_per_dag`) — https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html
- Airflow deferrable operators and the triggerer — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/deferring.html
- Google Cloud Composer: choosing an environment size — https://cloud.google.com/composer/docs/how-to/managing/environments
- Google Cloud Composer: managing DAGs — https://cloud.google.com/composer/docs/how-to/managing/creating
