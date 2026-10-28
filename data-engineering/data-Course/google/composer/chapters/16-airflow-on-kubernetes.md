# 5.16 — Airflow on Kubernetes

> **Section 5 · Engineering Practice · Lecture 5.16 · 7:30**

## 🎯 What you will learn

- Why teams put Airflow on Kubernetes, and what they are actually buying
- The `KubernetesExecutor` model in detail: one Pod per task, no worker pool
- Pod templates: what you supply, what Airflow fills in, and per-task templates
- RBAC and namespaces: the exact permissions required, and how to verify them
- Resource requests and limits, and the three ways a Pod fails to start
- The CNI plugin: what it is, why it matters for egress, and how to configure it
- The **30–60 second pod startup cost**, and how to decide whether it is acceptable
- Airflow 2.x improvements to the KubernetesExecutor
- How all of this relates to Cloud Composer, and when to use which

---

## 🧠 Concept

### Why Kubernetes for Airflow

Before Kubernetes, the options for running Airflow at scale were a list of machines with a broker in the middle, or a single large VM. Both have a specific failure mode: **the worker pool has a fixed shape**, and you have to guess it.

Kubernetes replaces the guess with a declaration:

```text
"Each task needs 2 vCPU and 4 GB. Give it exactly that, and run as many
 as the cluster can fit."
```

The five things teams genuinely get from running Airflow on Kubernetes:

**1. Per-task resource profiles.** A task that runs a Spark job wants 8 vCPU and 32 GB. A task that sends an email wants 100 millicores and 128 MB. With a homogeneous worker pool, both get the same size — so you either over-provision the email task or OOM the Spark task. With the KubernetesExecutor, each task gets a Pod built from its own template.

**2. Isolation.** Every task runs in its own container, in its own network namespace, with its own resource limits. A task that leaks memory cannot take down its neighbours, because there are no neighbours.

**3. Elasticity.** Workers exist only while they are running. An idle Airflow installation on Kubernetes costs the control plane, not a worker fleet. This is the opposite of Celery, where idle workers bill continuously.

**4. Environment parity.** The Airflow environment runs in the same cluster, the same network, the same IAM boundary as the data it processes. There is no VPN between "the orchestration cluster" and "the data cluster".

**5. Standardised operations.** Every Airflow environment is a set of Deployments and Services that your existing monitoring, logging, and autoscaling tooling already understands.

**And the costs, stated honestly:**

| Cost | Detail |
|---|---|
| **Startup latency** | 30–60 seconds per task, paid every time |
| **Cluster operations** | You now operate a Kubernetes cluster: upgrades, node pools, autoscaling, CNI, DNS |
| **RBAC complexity** | The scheduler needs permissions to create Pods; misconfiguration is a 403 |
| **Image management** | Every task's image is yours to build, tag, and patch |
| **Observability gaps** | A Pod's logs live in `kubectl logs`, not in the Airflow UI, unless you wire them up |
| **Cold-start variance** | Image pull time dominates on first use and after a node scale-up |

### The KubernetesExecutor model

The architecture is genuinely different from Celery, and understanding the difference is the key to everything else.

```text
┌──────────────────────────────────────────────────────────────────┐
│  CeleryExecutor                                                  │
│                                                                  │
│  Scheduler ──publish──▶ Broker (Redis/RabbitMQ) ◀──consume──┐   │
│                                                           │     │
│                                                   ┌───────▼──┐  │
│                                                   │ Worker 1 │  │
│                                                   │ Worker 2 │  │
│                                                   │ Worker 3 │  │
│                                                   └──────────┘  │
│   Long-lived workers. Idle workers cost money.                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  KubernetesExecutor                                              │
│                                                                  │
│  Scheduler ──create Pod──▶ Kubernetes API ◀──watch──┐            │
│      ▲                            │                  │            │
│      │                            ▼                  │            │
│      │                      ┌───────────┐            │            │
│      └────delete────        │ Pod: task │────────────┘            │
│                             │ Pod: task │                         │
│                             │ Pod: task │                         │
│                             └───────────┘                         │
│   One Pod per task. No Pods when idle. 30-60s to start.          │
└──────────────────────────────────────────────────────────────────┘
```

**The KubernetesExecutor has no worker pool.** There is no long-lived process waiting for work. The scheduler creates a Pod, the Pod runs one task, the Pod exits and is deleted.

**The consequences:**

| Question | Celery | Kubernetes |
|---|---|---|
| Where does a task run? | On any free worker | In a brand-new Pod |
| What is the startup cost? | ~0 (worker is already up) | **30–60 seconds** |
| What is the idle cost? | Worker fleet × hours | **Zero** |
| Can tasks have different resources? | No | **Yes** |
| Can tasks have different images? | No | **Yes** |
| What happens on worker death? | The task is redelivered to another worker | The Pod dies; the task is requeued and a new Pod is created |
| Where do the logs live? | In the worker's log stream | In the Pod's log, until it is deleted |

**Airflow 2.x's `KubernetesExecutor` improvements.** Between 2.0 and 2.9, the executor changed substantially:

| Version | Change |
|---|---|
| 2.0 | `KubernetesExecutor` became the recommended way to run Airflow on Kubernetes; `KubernetesPodOperator` added |
| 2.1 | `pod_template_file` replaces the old `kubernetes_container` YAML config; `in_cluster` split from `kube_config` |
| 2.2 | Deferrable operators — which work with the KubernetesExecutor, releasing the scheduler's Pod |
| 2.3 | Dynamic task mapping; `KubernetesPodOperator` supports `.expand()` |
| 2.4 | Datasets; `KubernetesExecutor` gains better `map_index` handling |
| 2.5 | `dag.test()` / `dag.run()` for local debugging |
| 2.6–2.9 | Steady improvements to Pod cleanup, `delete_operator_pod`, RBAC handling, and the `KubernetesPodOperator` |

The most consequential change for a designer is **2.2's deferrable operators**: with the KubernetesExecutor, a sensor that waits for six hours would otherwise hold a Pod (and a cluster slot) for six hours. With a deferrable sensor, the Pod exits and the triggerer resumes the task later — the cluster is released while you wait.

### Pod templates

The executor needs to know how to build a Pod. That is the pod template — a YAML file you supply.

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

**What you supply:** the container image, the resource requests and limits, the volumes, the service account, the labels, the node selectors, the tolerations, the security context.

**What Airflow fills in:** the Pod name (from `dag_id`, `task_id`, `run_id`, `try_number`, and the `map_index`), the command and arguments (`airflow tasks run ...`), the environment variables, the config map or secret references, and the volumes that carry the Airflow config.

**`name: dummy-name` is literal.** Airflow overwrites it. This is a well-known papercut — people copy a template with `dummy-name` and then wonder why the Pod name in `kubectl get pods` looks like `orders-etl-load-to-bigquery-20260115-0001-0` rather than `dummy-name`. It is supposed to.

**Per-task templates.** The real power is one template per task class:

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

heavy = KubernetesPodOperator(
    task_id="run_heavy_etl",
    name="heavy-etl",
    image="gcr.io/my-project/etl:2.9.3",
    pod_template_file="/opt/airflow/pod_templates/heavy.yaml",
    cmds=["python", "/opt/airflow/etl/run.py"],
    arguments=["{{ ds }}"],
    get_logs=True,
    is_delete_operator_pod=True,
)

light = KubernetesPodOperator(
    task_id="send_notification",
    name="notify",
    image="gcr.io/my-project/notify:1.4.2",
    pod_template_file="/opt/airflow/pod_templates/light.yaml",
    cmds=["python", "/opt/airflow/notify/send.py"],
    get_logs=True,
    is_delete_operator_pod=True,
)
```

`is_delete_operator_pod=True` is worth setting: it makes the operator delete the Pod when the task completes. Without it, the Pods pile up until Kubernetes garbage-collects them, and you accumulate a large, useless `Completed` list.

**`get_logs=True`** streams the Pod's output into the Airflow task log, which is what makes debugging possible. Without it, you are `kubectl logs`-ing a Pod that may already have been deleted.

### RBAC

The scheduler's service account needs to create, watch, and delete Pods in the namespace where tasks run.

```yaml
# rbac/pod-creator-role.yaml
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

And the binding:

```yaml
# rbac/pod-creator-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: airflow-pod-creator
  namespace: airflow
subjects:
  - kind: ServiceAccount
    name: airflow-scheduler
    namespace: airflow
roleRef:
  kind: Role
  name: airflow-pod-creator
  apiGroup: rbac.authorization.k8s.io
```

**When the binding is missing or wrong**, the scheduler's attempt to create the Pod fails:

```text
Pod creation failed: 403 Forbidden
```

And from the Kubernetes API, the full form:

```text
pods "orders-etl-load-to-bigquery-20260115-0001-0" is forbidden: User "system:serviceaccount:airflow:airflow-scheduler" cannot create resource "pods" in API group "" in the namespace "airflow"
```

That is the canonical KubernetesExecutor permission error, and it is **always** an RBAC problem. No amount of code change fixes it.

**Two more permissions people forget:**

| Permission | Why |
|---|---|
| `pods/log` → `get` | So `get_logs=True` can stream the Pod's output |
| `configmaps`/`secrets` → `get` | So the scheduler can read the Airflow config and the task's secrets |

**Verify before you deploy:**

```bash
kubectl auth can-i create pods \
  --as=system:serviceaccount:airflow:airflow-scheduler \
  -n airflow
# Expected: yes

kubectl auth can-i get pods/log \
  --as=system:serviceaccount:airflow:airflow-scheduler \
  -n airflow
# Expected: yes
```

### Namespaces

Tasks can run in a namespace other than the scheduler's. This is how you achieve isolation and placement.

```yaml
# In the DAG:
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

untrusted = KubernetesPodOperator(
    task_id="run_untrusted",
    namespace="tenant-a",           # ← different namespace
    pod_template_file="/opt/airflow/pod_templates/light.yaml",
    ...
)
```

**The RBAC implication.** A `Role` is namespace-scoped. If the scheduler creates Pods in `tenant-a`, the scheduler's service account needs a binding **in `tenant-a` too**. Either:

- A `Role` + `RoleBinding` in each target namespace, or
- A `ClusterRole` + `ClusterRoleBinding` (broader — grants the ability to create Pods in *every* namespace, which is a significant privilege).

The `ClusterRole` route is simpler and is what most Helm charts do. It is also a real security exposure: a compromised Airflow scheduler can create Pods anywhere in the cluster, and a Pod is a container with whatever permissions its service account has.

**Why namespaces matter for placement:**

| Goal | Mechanism |
|---|---|
| Run untrusted code away from Airflow | A separate namespace with a restrictive Pod Security Admission label |
| Pin a task to specific hardware | A node selector in the pod template |
| Isolate a noisy tenant | A separate namespace with its own ResourceQuota |
| Keep the Airflow control plane private | NetworkPolicy denying ingress to the `airflow` namespace from outside |

### Resource requests and limits

Every container needs both.

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "1"
    memory: "2Gi"
```

**Requests** drive scheduling and cost. The scheduler places a Pod on a node that has at least the requested amount free. Requests also determine your bill — in a cluster with cluster-autoscaler or a node autoscaler, the *requests* are what get provisioned.

**Limits** cap the container. A container that exceeds its memory limit is killed with `OOMKilled`:

```text
Status: 0 (Terminated)
Reason: OOMKilled
Exit Code: 137
```

Exit code 137 is SIGKILL — the kernel's OOM killer. It is the single most common Kubernetes task failure, and it means the memory limit was too low.

**The three ways a Pod fails to start**, and how each presents:

| Failure | Symptom | Fix |
|---|---|---|
| **No node fits** | `Pod creation failed: 0/3 nodes are available: 3 Insufficient cpu` | Lower the requests, add nodes, or fix the node selector |
| **Image cannot be pulled** | `ErrImagePull` / `ImagePullBackOff` | Add an `imagePullSecret`, or make the image public |
| **RBAC denied** | `403 Forbidden` | Fix the Role and RoleBinding |

Note the difference from the Celery world: with a long-lived worker pool, an under-resourced task causes an OOM kill on a worker that other tasks also use. With one Pod per task, an under-resourced task affects only itself — and the Pod is recreated cleanly on retry.

**The request/limit asymmetry.** A common and correct pattern is `requests == limits` for CPU (so the task gets a guaranteed share and is not throttled) and `requests < limits` for memory (so the task can burst, but is killed rather than starving the node). For a memory-hungry task, set them equal and size the limit from a measurement.

### The CNI plugin

Every Kubernetes Pod needs a network interface. The **CNI (Container Network Interface) plugin** provides it — a small binary that the kubelet invokes to attach a Pod to the network.

```text
Pod creation
    │
    ▼
kubelet sees a Pod with no network
    │
    ▼
kubelet invokes the CNI plugin (ADD operation)
    │
    ▼
plugin creates a network namespace, a veth pair, and the IPAM allocation
    │
    ▼
Pod has an IP address and can talk to the cluster
```

**Why it matters for Airflow specifically.**

Airflow tasks routinely make outbound calls: to BigQuery, to GCS, to an internal API, to a database. The CNI plugin's egress policy determines whether those calls work.

| CNI plugin | Egress behaviour | Consequence for Airflow |
|---|---|---|
| **Calico** | Full networking; `NetworkPolicy` supported | Tasks can reach anything, unless a NetworkPolicy forbids it |
| **Cilium** | Full networking; `NetworkPolicy` at L3/L4/L7 | Same, plus CiliumNetworkPolicy for finer control |
| **GKE Dataplane V2** | GKE-native; `NetworkPolicy` supported | Same |
| **An egress-blocking plugin** | Denies all egress by default | **Every Airflow task fails** to reach BigQuery/GCS |

**The failure looks like a timeout, not a permission error:**

```text
sqlalchemy.exc.OperationalError: (gcloud.bigquery.client.exceptions.Forbidden) 403 Getting BigQuery API failed
```

or, more confusingly:

```text
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='bigquery.googleapis.com', port=443): Max retries exceeded
```

Because the connection never establishes, the error is a timeout. **Always check the network path before you check IAM** when a task times out on its first outbound call.

**The configuration.** In Airflow, the network config is passed to the Pod via the `kubernetes_conn_id` Connection's extras:

```json
{
  "cluster_api_URL": "https://YOUR_CLUSTER_ENDPOINT",
  "in_cluster": false,
  "kube_config": {"cluster": "airflow", "namespace": "airflow"},
  "verify_ssl": true,
  "ssl_ca_cert": "/etc/ssl/certs/ca-certificates.crt"
}
```

And the network policies live in the cluster, not in Airflow:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: airflow-task-egress
  namespace: airflow
spec:
  podSelector:
    matchLabels:
      app: airflow
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8
      ports:
        - protocol: TCP
          port: 443
```

Note the `10.0.0.0/8` — GCP's private API ranges. When the cluster's nodes have private Google access, the BigQuery and GCS endpoints resolve to private IPs in `10.0.0.0/8`. A NetworkPolicy that only allows the public IP ranges will break the tasks in a confusing way.

### The pod startup cost

This is the number that decides whether the KubernetesExecutor is viable for your workload.

> **A Kubernetes Pod takes roughly 30–60 seconds to start.**

The breakdown:

| Phase | Duration | What happens |
|---|---|---|
| Scheduling | 1–5s | The scheduler finds a node with capacity |
| Image pull | 0–40s | Pull and unpack the image. **Zero on a warm node, 40s on a cold one** |
| Volume mount | 1–5s | Attach the PVC, mount ConfigMaps and Secrets |
| Container start | 1–3s | Start the container, run the entrypoint |
| Airflow handshake | 2–10s | The task process starts, imports Airflow, reads the config, connects to the DB, pulls the task |
| **Total** | **~30–60s** | |

**The image-pull term is the variable one.** A cluster with warm nodes and a pre-pulled image can start in 30 seconds; a fresh node with a 2 GB image can take 90 seconds.

**The arithmetic that matters:**

| Task runtime | Startup overhead | Efficiency |
|---|---|---|
| 5s | 45s | 10% |
| 30s | 45s | 40% |
| 1min | 45s | 57% |
| 5min | 45s | 87% |
| 45min | 45s | 98% |

**The rule: the KubernetesExecutor is right for heavy tasks and wrong for chatty ones.** A DAG with 100 tasks that each take 3 seconds is a disaster: 100 × 45s = 75 minutes of pure startup.

**Mitigations, in order of effectiveness:**

1. **Make the tasks heavier.** Batch the work so each task takes minutes, not seconds.
2. **Reduce the task count.** Combine small tasks into one, or use dynamic task mapping over *larger* units of work.
3. **Pre-pull the images.** A DaemonSet that pulls your Airflow image onto every node eliminates the 40-second image pull from steady state.
4. **Use a warm node pool.** Keep one node warm with the images already on it.
5. **Use dynamic task mapping so the Pods start in parallel.** This turns 100 sequential startups into 100 concurrent startups — the wall time becomes 45 seconds, not 75 minutes.

### Airflow 2.x improvements, in one place

| Version | Feature | Practical effect |
|---|---|---|
| 2.0 | `KubernetesExecutor` production-hardened; `KubernetesPodOperator` added | You can run whole DAGs in Pods, not just individual tasks |
| 2.1 | `pod_template_file` replaces the old config; `in_cluster` / `kube_config` split | Templates are per-task files; in-cluster auth is separate from kubeconfig |
| 2.2 | **Deferrable operators** | A waiting task releases its Pod; the triggerer resumes it later |
| 2.3 | **Dynamic task mapping** | One task definition, N Pods, created in parallel |
| 2.4 | **Datasets** | Event-driven scheduling without cross-DAG name coupling |
| 2.5 | `dag.test()` / `dag.run()` | Debug a DAG locally without a cluster |
| 2.6–2.9 | Pod cleanup, `is_delete_operator_pod`, better `map_index` handling, RBAC hardening | Fewer orphan Pods; more reliable mapped-task naming |

The two that change the architecture most are **2.2's deferrable operators** and **2.3's dynamic task mapping**. Together they mean: one task definition, N Pods started in parallel, and no Pod held while waiting.

### How this relates to Composer

Cloud Composer is Airflow, managed. You do not run the cluster, the scheduler, the workers, or the triggerer.

| | Self-managed Airflow on Kubernetes | Cloud Composer |
|---|---|---|
| The cluster | yours | Google's |
| The scheduler | yours | managed |
| The workers | your Celery fleet or KubernetesExecutor | managed |
| The pod templates | yours | not exposed |
| RBAC | yours | managed |
| CNI | yours | managed |
| The 30–60s startup | yes, if you use the KubernetesExecutor | **no** — Composer's workers are long-lived |
| Autoscaling | yours | yours (environment size) |
| Airflow version | you choose | you choose, within the supported range |
| Cost | cluster + nodes + your time | per-environment, per-worker |

**The key difference in behaviour.** Composer's default is a **long-lived worker pool** (CeleryExecutor), so a task starts in seconds, not a minute. A Composer environment on the KubernetesExecutor does have the pod-startup cost — but Composer manages the cluster, the CNI, the RBAC, and the node autoscaling, so you get the per-task resource flexibility without the operational burden.

**When to use which:**

| Situation | Recommendation |
|---|---|
| You want managed Airflow and standard task sizes | **Composer, CeleryExecutor** — the default, and the right answer |
| You want managed Airflow and heavy tasks with varied resource needs | **Composer with the KubernetesExecutor** — you get per-task Pods without running the cluster |
| You need to run Airflow inside your own cluster, with strict network or data residency requirements | **Self-managed Airflow on Kubernetes** |
| You want to avoid a vendor's Airflow version pinning | **Self-managed** — but you own the upgrade burden |
| You need per-task images that Composer cannot host | Self-managed, or use `KubernetesPodOperator` from Composer (which can reference images in your own registry) |

**The pragmatic recommendation:** if you are on Google Cloud and your tasks are ordinary (queries, API calls, moderate Python), use **Composer with the default executor**. The KubernetesExecutor's benefits — per-task resources, per-task images — are real but usually not worth the startup tax at typical task durations.

---

## 🛠️ Hands-On

### Step 1 — inspect the course's DAGs for Kubernetes-relevant properties

```bash
cd data-engineering/data-Course/google/composer
python3 project/local_runner.py --describe --dag all
```

Expected output:

```text
DAG: branching_load
  schedule    : @daily
  start_date  : 2026-01-01
  catchup     : False
  description : Pick a full-load or incremental strategy based on row volume.
  tasks (6):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - choose_strategy        deps=(transform_orders) [branch]
    - full_load              deps=(choose_strategy)
    - incremental_load       deps=(choose_strategy)
    - finalise               deps=(full_load, incremental_load) [rule=none_failed]

DAG: etl_to_gcs
  ...
  tasks (4):
    - read_orders            deps=(-)
    - transform_orders       deps=(read_orders)
    - aggregate              deps=(transform_orders)
    - write_summary          deps=(aggregate)

DAG: templating_paths
  ...
DAG: xcom_pipeline
  ...
```

**Read this for the Kubernetes question.** Every DAG is a **chain** — at most one task is ever ready at a time. That means the Pod-startup tax is paid *sequentially*:

```text
etl_to_gcs on the KubernetesExecutor:
  read_orders        45s startup + work
  transform_orders   45s startup + work
  aggregate          45s startup + work
  write_summary      45s startup + work
                      ─────────
                      180s of pure startup, for a DAG whose work is ~20ms
```

This is the concrete calculation that decides the executor, and it is why the course's DAGs belong on a long-lived worker pool.

### Step 2 — measure the real task durations

```bash
python3 - <<'PY'
import sys, time
sys.path.insert(0, "project/core")
from pipeline_logic import transform_orders, summarise_by_region, render_summary_csv

lines = open("sample_data/orders.csv").read().splitlines()
accepted, rejected = transform_orders(lines)   # returns a (accepted, rejected) tuple

timings = {}
for name, fn in (
    ("transform_orders", lambda: transform_orders(lines)),
    ("summarise_by_region", lambda: summarise_by_region(accepted)),
    ("render_summary_csv", lambda: render_summary_csv(summarise_by_region(accepted))),
):
    start = time.perf_counter()
    fn()
    timings[name] = (time.perf_counter() - start) * 1000

for name, ms in timings.items():
    print(f"{name:<24} {ms:>8.2f} ms")
print()
print(f"total pure compute: {sum(timings.values()):.2f} ms")
PY
```

Expected output (approximately):

```text
transform_orders          12.99 ms
summarise_by_region        0.23 ms
render_summary_csv         0.22 ms

total pure compute: 13.43 ms
```

**Now apply the rule.** The tasks take milliseconds. The Pod startup is 45 seconds — **3,000× the work**. The KubernetesExecutor would spend 99.97% of its time creating Pods.

### Step 3 — compute the startup tax for each DAG

```bash
python3 - <<'PY'
"""What would the KubernetesExecutor cost for each course DAG?"""
import sys
sys.path.insert(0, "project")
from local_runner import DAGS

POD_STARTUP = 45          # seconds
TASK_WORK = 0.02          # seconds of real work per task (measured)

print(f"{'dag':<18} {'tasks':>6} {'startup':>9} {'work':>7} {'efficiency':>12}")
print("-" * 58)
for name in ("etl_to_gcs", "templating_paths", "xcom_pipeline", "branching_load"):
    dag = DAGS[name]()
    n = len(dag.tasks)
    startup = n * POD_STARTUP
    work = n * TASK_WORK
    eff = work / (startup + work) * 100
    print(f"{name:<18} {n:>6} {startup:>7}s {work:>6.2f}s {eff:>11.3f}%")
print()
print("Efficiency = time doing useful work / total time.")
print("Anything below ~50% means the executor choice is wrong for this DAG.")
PY
```

Expected output:

```text
dag                tasks  startup     work   efficiency
----------------------------------------------------------
etl_to_gcs             4     180s   0.08s       0.044%
templating_paths       4     180s   0.08s       0.044%
xcom_pipeline          5     225s   0.10s       0.044%
branching_load         6     270s   0.12s       0.044%

Efficiency = time doing useful work / total time.
Anything below ~50% means the executor choice is wrong for this DAG.
```

### Step 4 — compute the same table for a realistic workload

The course's data is tiny. Here is the same calculation for a production-shaped DAG, so the comparison is honest.

```bash
python3 - <<'PY'
"""Compare executor efficiency across task durations."""
POD_STARTUP = 45
CELERY_DISPATCH = 0.5

print(f"{'task duration':>14} {'celery wall':>12} {'k8s wall':>10} {'k8s overhead':>13} {'k8s faster?':>13}")
print("-" * 70)
for work in (1, 5, 30, 120, 600, 3600):
    celery = CELERY_DISPATCH + work
    k8s = POD_STARTUP + work
    overhead = (k8s - celery) / celery * 100
    faster = "YES" if k8s < celery else "no"
    print(f"{work:>12}s {celery:>11.1f}s {k8s:>9.1f}s {overhead:>12.0f}% {faster:>13}")
PY
```

Expected output:

```text
 task duration   celery wall    k8s wall  k8s overhead  k8s faster?
----------------------------------------------------------------------
            1s         1.5s       46.0s       2967%            no
            5s         5.5s       50.0s        809%            no
           30s        30.5s       75.0s        146%            no
          120s       120.5s      165.0s         37%            no
          600s       600.5s      645.0s          7%            no
         3600s      3600.5s     3645.0s           1%            no
```

Read that last column honestly: **on wall-clock time alone, Kubernetes never wins.** The 45-second startup is a fixed tax that Celery's warm worker does not pay, so for a single task in isolation Kubernetes is always slower.

Kubernetes earns its cost elsewhere:

| What you pay for | Celery | Kubernetes |
|---|---|---|
| Per-task startup | ~0.5s | ~45s |
| Idle capacity | a warm worker costs money 24/7 | a Pod exists only while the task runs |
| Per-task CPU / memory | whatever the worker has | exact requests and limits, per task |
| Isolation | shared process space | a fresh Pod, fresh filesystem |
| Heterogeneous dependencies | one image for every task | a different image per task |
| Spot / preemptible nodes | not really | naturally, via `nodeSelector` + `tolerations` |

**The practical rule:** use Kubernetes when a task is long (minutes to hours) or needs its own image, its own resources, or its own scheduling policy. Use Celery when tasks are short, share a single image, and the DAG is wide. The crossover is around **7–8 minutes** of task duration — below it the 45-second tax dominates, above it the isolation and cost elasticity dominate.

That is the whole decision, in one table.

### Step 5 — write the pod template

```yaml
# kubernetes/pod_templates/base.yaml
apiVersion: v1
kind: Pod
metadata:
  name: dummy-name
  labels:
    app: airflow
    component: task
spec:
  restartPolicy: Never
  serviceAccountName: airflow-worker
  automountServiceAccountToken: true
  containers:
    - name: base
      image: gcr.io/YOUR_PROJECT_ID/airflow:2.9.3
      imagePullPolicy: IfNotPresent
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
      env:
        - name: AIRFLOW__CORE__DAGS_FOLDER
          value: /opt/airflow/dags
      volumeMounts:
        - name: airflow-logs
          mountPath: /opt/airflow/logs
        - name: airflow-config
          mountPath: /opt/airflow/config
  volumes:
    - name: airflow-logs
      persistentVolumeClaim:
        claimName: airflow-logs
    - name: airflow-config
      configMap:
        name: airflow-config
```

Two details worth calling out:

- **`imagePullPolicy: IfNotPresent`** is the single most effective startup optimisation. `Always` re-checks the registry on every Pod start, which adds seconds per task and, worse, means a new Pod pulls a new image even when the tag has not changed.
- **`restartPolicy: Never`** is required. Airflow manages retries itself; a restarting Pod would fight the executor's retry logic.

### Step 6 — write and apply the RBAC

```bash
kubectl create namespace airflow

kubectl create role airflow-pod-creator \
  --namespace airflow \
  --verb=create,get,list,watch,delete \
  --resource=pods

kubectl create rolebinding airflow-pod-creator \
  --namespace airflow \
  --role=airflow-pod-creator \
  --serviceaccount=airflow:airflow-scheduler
```

Add the `pods/log` permission:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: airflow-pod-logger
  namespace: airflow
rules:
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get", "list"]
```

Verify:

```bash
kubectl auth can-i create pods \
  --as=system:serviceaccount:airflow:airflow-scheduler -n airflow
# Expected: yes

kubectl auth can-i get pods/log \
  --as=system:serviceaccount:airflow:airflow-scheduler -n airflow
# Expected: yes
```

If either says `no`, the scheduler will fail with `Pod creation failed: 403 Forbidden`.

### Step 7 — the Airflow configuration

```ini
# airflow.cfg
[core]
executor = KubernetesExecutor
dags_folder = /opt/airflow/dags
parallelism = 32
max_active_tasks_per_dag = 16

[kubernetes]
namespace = airflow
pod_template_file = /opt/airflow/pod_templates/base.yaml
delete_operator_pod = True
get_logs = True
in_cluster = True
cluster_api_URL = https://kubernetes.default.svc

[kubernetes_secrets]
# Airflow reads its connections and variables from these secrets.
```

And the Kubernetes connection, with the network extras:

```json
{
  "conn_id": "kubernetes_default",
  "conn_type": "kubernetes",
  "description": "Airflow's own cluster",
  "extra": {
    "cluster_api_URL": "https://YOUR_CLUSTER_ENDPOINT",
    "in_cluster": true,
    "verify_ssl": true
  }
}
```

### Step 8 — write a DAG that uses the KubernetesExecutor

```python
# project/dags/12_kubernetes_tasks.py
"""
12_kubernetes_tasks.py — running tasks in Kubernetes Pods.

Demonstrates:
  * `KubernetesPodOperator` with a per-task pod template
  * per-task resource profiles
  * `is_delete_operator_pod` and `get_logs`
  * dynamic task mapping over a Pod operator

The DAG itself runs on the scheduler; only the *tasks* become Pods.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

log = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def list_regions(**context) -> list[str]:
    """Return the regions to process.

    Args:
        context: The Airflow task context.

    Returns:
        A list of region codes.
    """
    from fanout import regions_to_process
    from pipeline_logic import summarise_by_region, transform_orders

    raw = context["ti"].xcom_pull(task_ids="read_orders") or []
    accepted, _ = transform_orders(raw)
    return regions_to_process(summarise_by_region(accepted))


def read_orders(**context) -> list[str]:
    """Read the raw order lines.

    Args:
        context: The Airflow task context.

    Returns:
        The raw CSV lines.
    """
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "sample_data" / "orders.csv"
    return path.read_text(encoding="utf-8").splitlines()


with DAG(
    dag_id="kubernetes_tasks",
    description="Run compute-heavy tasks in Kubernetes Pods.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["tutorial", "kubernetes"],
) as dag:
    read = PythonOperator(task_id="read_orders", python_callable=read_orders)

    regions = PythonOperator(task_id="list_regions", python_callable=list_regions)

    # A per-region Pod. Every mapped instance gets its own Pod, and
    # they are created in parallel — so the 45-second startup is paid
    # once, not once per region.
    process = KubernetesPodOperator.partial(
        task_id="process_region",
        name="process-region",
        image="gcr.io/YOUR_PROJECT_ID/airflow:2.9.3",
        cmds=["python", "/opt/airflow/jobs/process_region.py"],
        arguments=["{{ params.region }}", "{{ ds }}"],
        get_logs=True,
        is_delete_operator_pod=True,
        in_cluster=True,
        reattach_on_restart=True,
    ).expand(region=regions.output)

    summary = PythonOperator(
        task_id="summarise",
        python_callable=lambda **ctx: {"regions": ctx["ti"].xcom_pull(task_ids="process_region")},
    )

    read >> regions >> process >> summary
```

### Step 9 — verify the underlying pipeline is unchanged

```bash
python3 project/local_runner.py --dag etl_to_gcs --date 2026-01-15
```

Expected tail:

```text
region,order_count,revenue_eur
AMER,318,113592.19
APAC,285,108194.92
EMEA,322,118423.22
LATAM,320,110646.18
```

### Step 10 — simulate the pod lifecycle, so the failure modes are concrete

```bash
python3 - <<'PY'
"""Simulate the KubernetesExecutor's Pod lifecycle and failure modes."""
import random

POD_STARTUP = 45
FAILURE_MODES = [
    ("Pod creation failed: 403 Forbidden",          0.10),  # missing RBAC
    ("Pod creation failed: 0/3 nodes are available",  0.05),  # no capacity
    ("ErrImagePull / ImagePullBackOff",               0.10),  # image not pullable
    ("OOMKilled (exit code 137)",                     0.05),  # memory limit too low
]

# A realistic 20-task DAG, each task 8 minutes of work.
TASKS = 20
WORK = 480

print(f"Simulating {TASKS} tasks, {WORK}s of work each, {POD_STARTUP}s startup\n")
random.seed(7)
attempts = 0
failures = []
for i in range(TASKS):
    attempts += 1
    failed = False
    for message, probability in FAILURE_MODES:
        if random.random() < probability:
            failures.append(message)
            attempts += 1        # Airflow retries the task
            failed = True
            break
    status = "retried" if failed else "ok"
    print(f"  task[{i:>2}]  startup={POD_STARTUP}s work={WORK}s  {status}")

print(f"\ntotal pod creations: {attempts}  (retries: {attempts - TASKS})")
print("failure modes seen:")
for message, _ in FAILURE_MODES:
    count = failures.count(message)
    if count:
        print(f"  {count}x  {message}")
print()
print("Every failure above is a configuration problem, not a code problem:")
print("  403            -> fix the Role and RoleBinding")
print("  no capacity    -> lower the requests or add nodes")
print("  image pull     -> add an imagePullSecret")
print("  OOMKilled      -> raise the memory limit")
PY
```

Expected output (approximately — the exact counts follow from `random.seed(7)`):

```text
Simulating 20 tasks, 480s of work each, 45s startup

  task[ 0]  startup=45s work=480s  ok
  task[ 1]  startup=45s work=480s  retried
  task[ 2]  startup=45s work=480s  retried
  task[ 3]  startup=45s work=480s  retried
  ...
total pod creations: 26  (retries: 6)
failure modes seen:
  1x  Pod creation failed: 403 Forbidden
  3x  Pod creation failed: 0/3 nodes are available
  2x  ErrImagePull / ImagePullBackOff
```

Six extra Pod creations for twenty tasks — a 30% overhead from configuration mistakes alone, before any genuine task failure. Note what the numbers say: **not one of those six failures was a bug in your code.** Every one was a missing Role, a missing capacity, or a missing image. On Kubernetes, "my task failed" usually means "my cluster is misconfigured," and the Pod's own status is where you look.

---

## 🛠️ Common Errors and Fixes

### `Pod creation failed: 403 Forbidden`

The scheduler could not create the task's Pod.

**Cause:** the scheduler's service account lacks `create` on `pods` in the target namespace.

**Fix:** create the Role and RoleBinding, then verify:

```bash
kubectl auth can-i create pods \
  --as=system:serviceaccount:airflow:airflow-scheduler -n airflow
```

The full API error names the exact problem:

```text
pods "..." is forbidden: User "system:serviceaccount:airflow:airflow-scheduler" cannot create resource "pods" in API group "" in the namespace "airflow"
```

### `Pod creation failed: 0/3 nodes are available: 3 Insufficient cpu`

**Cause:** no node has enough free capacity for the Pod's requests.

**Fix:** lower the `requests` in the pod template, add nodes, or fix the node selector so it matches nodes that actually exist:

```bash
kubectl get nodes -l accelerator=gpu
```

### `ErrImagePull` / `ImagePullBackOff`

**Cause:** the Pod cannot pull its image — the registry requires authentication, or the image does not exist at that tag.

**Fix:**
```bash
kubectl create secret docker-registry regcred \
  --docker-server=gcr.io \
  --docker-username=json_key \
  --docker-password="$(cat key.json)" \
  --namespace=airflow
```
And reference it in the pod template:
```yaml
spec:
  imagePullSecrets:
    - name: regcred
```

For GCR/Artifact Registry, use a service-account-based image pull secret rather than a basic one.

### The task failed with exit code 137 / `OOMKilled`

**Cause:** the container exceeded its memory limit and the kernel killed it.

**Fix:** raise the limit, and lower the request if the task genuinely needs less than you gave it:

```yaml
resources:
  requests:
    memory: "2Gi"
  limits:
    memory: "4Gi"
```

Then check the Pod's actual peak usage before settling on a number:
```bash
kubectl top pod <pod-name> --namespace=airflow
```

### The task times out on its first outbound call to BigQuery

**Cause:** the CNI plugin or a NetworkPolicy is blocking egress. Because the connection never establishes, the error is a *timeout*, not a 403.

**Fix:** check the network path first.
```bash
kubectl exec -it <pod-name> --namespace=airflow -- \
  curl -sS -o /dev/null -w "%{http_code}\n" https://bigquery.googleapis.com/
```
If that hangs, it is the network. Check the NetworkPolicies and, on GKE, whether Private Google Access is enabled and whether the policy allows `10.0.0.0/8`.

### The Pod name is `dummy-name` in the logs but something else in `kubectl get pods`

**Cause:** that is expected. Airflow overwrites the `metadata.name` from the template with a generated name.

**Fix:** nothing. But do change `dummy-name` to something meaningful anyway — it appears in the rendered template and in error messages, and a clear placeholder makes the rendered YAML readable.

### The Pods are not being deleted and the namespace is full of `Completed` Pods

**Cause:** `is_delete_operator_pod` is not set (or `delete_operator_pod` is not in `airflow.cfg`).

**Fix:** set `is_delete_operator_pod=True` on the operator, and `delete_operator_pod = True` in the `[kubernetes]` section of `airflow.cfg`.

```bash
kubectl delete pods --namespace airflow --field-selector=status.phase=Failed
```

### The task starts but immediately fails with an Airflow import error

**Cause:** the Pod's image does not have the same Airflow version and provider packages as the scheduler.

**Fix:** pin the image to the exact Airflow version the cluster runs, and include the providers the DAG needs. Verify:
```bash
kubectl exec -it <pod-name> --namespace=airflow -- \
  airflow version
```

### `Max number of active tasks allowed (16) reached`

**Cause:** too many tasks running at once for the DAG's `max_active_tasks_per_dag`.

**Fix:** raise the limit (and the cluster's capacity to match), or lower the fan-out. Remember that with the KubernetesExecutor, a higher limit means more concurrent Pods — which means more nodes and more money.

### The Airflow UI shows the task as queued for minutes before it starts

**Cause:** the Pod-startup tax, plus any cluster autoscaling delay.

**Fix:** pre-pull images with a DaemonSet, use `imagePullPolicy: IfNotPresent`, keep a warm node pool, and reduce the number of tasks.

### The triggerer never resumes a deferred task

**Cause:** the triggerer process is not running (self-managed), or it crashed.

**Fix:** check the triggerer deployment:
```bash
kubectl get pods --namespace airflow -l app=triggerer
kubectl logs --namespace airflow -l app=triggerer --tail=50
```

### `airflow.exceptions.DagNotFound: DAG: [my_dag] not found`

**Cause:** the DAG file is on a shared volume that the *scheduler* can see, but the task Pod cannot — or vice versa.

**Fix:** ensure the DAGs folder is mounted in both the scheduler Deployment and the pod template's volumes. A DAG that the scheduler can parse but the Pod cannot import will fail in the Pod with an import error, and the task will retry forever.

---

## 💡 Production Notes

- **The KubernetesExecutor is for heavy tasks.** The crossover is around **7–8 minutes** of task duration; below that, a long-lived worker pool wins on wall time. The course's DAGs take milliseconds and belong on Celery.
- **Measure your task durations before choosing.** "Our tasks take 45 minutes" and "our tasks take 30 seconds" are the same system with completely different right answers.
- **`imagePullPolicy: IfNotPresent` and a pre-pull DaemonSet** remove most of the variable part of the 45-second startup.
- **Set `is_delete_operator_pod=True`.** Orphaned `Completed` Pods accumulate until Kubernetes garbage-collects them, and they cost cluster capacity and confuse every human reading `kubectl get pods`.
- **Always grant `pods/log` → `get`** if you use `get_logs=True`. Without it, the operator cannot stream the Pod's output into the Airflow task log, and you are `kubectl logs`-ing a Pod that may already be gone.
- **403 Forbidden is always RBAC.** Do not debug it as a code problem. `kubectl auth can-i` answers it in one second.
- **A timeout on the first outbound call is a network problem until proven otherwise.** Check the CNI plugin and NetworkPolicies before you check IAM.
- **On GKE with Private Google Access, the Google APIs resolve to `10.0.0.0/8`.** A NetworkPolicy that allows only public IP ranges will break your tasks in a way that looks like a timeout.
- **Requests drive cost and scheduling; limits drive correctness.** Set CPU request == limit for predictable throughput; set memory request == limit for a task whose peak you have measured.
- **A `ClusterRole` for the scheduler is a real security exposure.** It lets a compromised scheduler create Pods anywhere in the cluster. Prefer namespace-scoped `Role`s.
- **Use namespaces deliberately:** isolation, quotas, node placement, and Pod Security Admission labels are all namespace-scoped.
- **On Composer, the default CeleryExecutor has no startup tax.** Choose the KubernetesExecutor only when you need per-task resources or per-task images, and accept the 45-second cost knowingly.

---

## 🔑 Key Takeaways

- Kubernetes gives Airflow **per-task resources, per-task images, isolation, zero idle cost, and environment parity** — in exchange for **30–60s of startup per task** and owning a cluster.
- The KubernetesExecutor has **no worker pool**: one Pod per task, created and destroyed.
- **Pod templates** supply the image, resources, volumes, and placement; Airflow fills in the name, command, args, and environment.
- **RBAC is the first thing to check** for `Pod creation failed: 403 Forbidden`. Verify with `kubectl auth can-i create pods`.
- **Namespaces** scope both placement and permissions; a `ClusterRole` for the scheduler is a genuine security exposure.
- **Requests** drive scheduling and cost; **limits** drive correctness. `OOMKilled` (exit 137) means the memory limit was too low.
- **The CNI plugin determines egress.** A blocked egress path shows up as a *timeout*, not a permission error.
- **The crossover is around 7–8 minutes of task duration.** Below that, Celery's zero startup wins; above it, Kubernetes wins on everything else.
- **The biggest Airflow 2.x wins for this model** are deferrable operators (2.2, releases the Pod while waiting) and dynamic task mapping (2.3, starts Pods in parallel).
- **Composer is Airflow, managed.** Its default CeleryExecutor has no startup tax; the KubernetesExecutor gives you per-task Pods without running the cluster.

---

## 📚 Practice Exercises

1. **Find the crossover precisely.** Using the table from the hands-on, compute the exact task duration at which a KubernetesExecutor task's total time equals a Celery task's total time, for a 30-second Celery dispatch and a 45-second Pod startup. Then compute it again for a 90-second Pod startup (a cold node with a large image). *Expected answer:* with a 45-second startup and a 0.5-second dispatch, the crossover is where `45 + work = 0.5 + work` — which never crosses, so the Celery task is always faster in wall time; the honest framing is that Kubernetes never wins on *latency for a single task*, it wins on *isolation, per-task resources, and idle cost*. With a 90-second startup the penalty is worse. The practical crossover — where the 45 seconds is under ~10% of the task's total time — is around 7–8 minutes.

2. **Write the complete RBAC for a two-namespace deployment.** An Airflow scheduler in `airflow` creates Pods in `airflow` and in `tenant-a`. Write the Roles, RoleBindings, and ServiceAccounts for both, then explain what a `ClusterRole` + `ClusterRoleBinding` would change and why it is a security downgrade. *Expected answer:* two `Role`s (one per namespace), each with `pods` create/get/list/watch/delete and `pods/log` get, plus a `RoleBinding` in each namespace binding the *same* `airflow:airflow-scheduler` ServiceAccount. The `ClusterRole` version grants one binding that covers every namespace, which means a compromised scheduler can create a Pod anywhere — and a Pod is arbitrary code with its service account's permissions. The downgrade matters most in multi-tenant clusters.

3. **Diagnose the OOMKilled task.** A Pod fails with exit code 137. Explain exactly what happened, why `kubectl describe pod` shows `Reason: OOMKilled`, and what to change. Then explain what would happen if the *request* were 2 Gi and the *limit* were 8 Gi, versus a request of 8 Gi and a limit of 8 Gi. *Expected answer:* the container exceeded its memory limit and the kernel's OOM killer sent SIGKILL (exit 137). The fix is to raise the limit after measuring the task's actual peak usage (`kubectl top pod`), and to set requests == limits for memory so the task is guaranteed its working set rather than being throttled or evicted. With request 2 Gi / limit 8 Gi, the Pod is scheduled onto a node with only 2 Gi free and can burst to 8 Gi if the node has it — efficient but eviction-prone; with 8/8, the node must have 8 Gi free, which is safer but reserves more capacity.

4. **Fix the egress timeout.** A task in the KubernetesExecutor fails with `requests.exceptions.ConnectTimeout` on its first call to `bigquery.googleapis.com`. The service account has `roles/bigquery.jobUser`, and the task works fine on a different namespace. Write the diagnostic sequence and the likely fix for a GKE cluster with Private Google Access. *Expected answer:** the sequence is: (1) `kubectl exec` into the Pod and `curl https://bigquery.googleapis.com/` — if it hangs, it is the network, not IAM; (2) list the NetworkPolicies in the namespace; (3) check whether the policy's egress allows `10.0.0.0/8` — with Private Google Access, the Google API endpoints resolve to private IPs in that range, so a policy allowing only public ranges blocks the call while appearing to allow "the internet"; (4) compare with the working namespace's policies. The fix is to add an egress rule for `10.0.0.0/8` on port 443, or to disable Private Google Access for that cluster.

5. **Convert a chatty DAG to a heavy one.** A DAG has 120 tasks, each taking 4 seconds, on the KubernetesExecutor. Compute the wall time and the Pod-creation count. Then redesign it three ways — (a) combine into 6 tasks of 80 seconds, (b) use dynamic task mapping over 30 units of 16 seconds, (c) keep 120 tasks but move the whole DAG to a Celery worker pool — and compute each one's wall time and Pod count. *Expected answer:* (original) 120 × (45 + 4) = 5,880s = 98 minutes, 120 Pods. (a) 6 × (45 + 80) = 750s = 12.5 minutes, 6 Pods. (b) the Pods start in parallel: 45 + 16 = 61s, 30 Pods. (c) 120 × (0.5 + 4) = 540s = 9 minutes, 0 Pods. The lesson: dynamic task mapping turns the startup tax from a *serial* cost into a *one-off parallel* cost, which is why it is the single most valuable Airflow 2.3 feature for Kubernetes users.

6. **Write the Composer decision.** Given three DAGs — (a) a nightly 40-minute Spark job on a persistent Dataproc cluster, (b) a 30-second BigQuery query that depends on another DAG, (c) a 3-hour Python job that must be isolated and run with 64 GB — recommend an execution model for each, and state what you would use on Composer versus self-managed Kubernetes. *Expected answer:* (a) the persistent Dataproc cluster should be ephemeral, and the Spark job should be moved to a BigQuery query or a Dataflow batch job if it is really a join-and-aggregate; on Composer, `SparkSubmitOperator` with an ephemeral cluster, or better, migrate the logic; (b) Composer with `BigQueryExecuteQueryOperator` — the dependency is the reason it needs Airflow, and the environment should be small since the compute is server-side; (c) self-managed Kubernetes on the KubernetesExecutor, because it needs 64 GB and isolation — Composer's default worker shape will not fit it. The general principle to state: Composer for standard workloads with dependencies; self-managed Kubernetes only when a specific requirement (resource shape, isolation, residency, custom images) genuinely cannot be met by a Composer environment.

---

## 📖 Further Reading

- Airflow KubernetesExecutor documentation — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/kubernetes.html
- Airflow `KubernetesPodOperator` API — https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/providers/cncf/kubernetes/operators/pod/index.html
- Airflow dynamic task mapping — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dynamic-task-mapping.html
- Airflow deferrable operators and the triggerer — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/deferring.html
- Kubernetes: pod templates and resource management — https://kubernetes.io/docs/concepts/workloads/pods/pod-templates/
- Kubernetes: RBAC good practices — https://kubernetes.io/docs/concepts/security/rbac-good-practices/
- Kubernetes: network policies — https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Kubernetes: Container Network Interface (CNI) — https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/
- Kubernetes: resource requests and limits — https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Kubernetes: Pod Security Admission — https://kubernetes.io/docs/concepts/security/pod-security-admission/
- Google Cloud Composer: choosing an environment and executor — https://cloud.google.com/composer/docs/how-to/managing/environments
- Google Cloud Composer: KubernetesExecutor — https://cloud.google.com/composer/docs/how-to/manage-environment-using-k8s-executor
