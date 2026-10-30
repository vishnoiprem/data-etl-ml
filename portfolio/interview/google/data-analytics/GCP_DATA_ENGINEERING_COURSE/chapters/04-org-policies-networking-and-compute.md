# 1.4 — Organization Policies, Networking & Compute

> **Section 1 · GCP Fundamentals · Lecture 1.4 · 8:00**

## 🎯 What you will learn
- The critical distinction between **Organization Policy** and **IAM**, and how confusing them causes outages
- What VPC networks actually are, and how a project relates to them
- Firewall rules, priorities and the default deny — and why ingress from 0.0.0.0/0 is a recurring incident
- The compute family end to end: Compute Engine, App Engine, GKE, Cloud Run, Cloud Run functions
- Containers and Docker, and how an image becomes a running service on GCP
- Artifact Registry, and why "push a container" needs a registry before it needs a cluster
- How to pick between the compute options with a decision matrix

---

## 🧠 Concept

### Organization Policy vs IAM: the distinction that causes outages

These are two different control systems that solve two different problems, and almost every "someone could delete the production bucket" incident traces back to confusing them.

**IAM answers "who may act."** A principal has a role; the role contains permissions; the permission is evaluated against a resource. IAM is about **identity**.

**Organization Policy answers "what may exist."** An organization policy constraint is attached to an organization, folder or project, and it limits the *configuration* of resources created beneath it. IAM is not involved in the decision at all. Organization Policy is about **configuration**.

Concrete examples of each:

| Organization Policy constraint | What it prevents | IAM analogue |
|---|---|---|
| `constraints/compute.disableSerialPortAccess` | Anyone attaching a serial console to a VM | None — IAM has no equivalent |
| `constraints/compute.restrictXpnProjectLienRemoval` | Anyone deleting a shared-VPC service project | None |
| `constraints/gcp.resourceLocations` | Creating a bucket in a disallowed region | None |
| `constraints/sql.restrictPublicIp` | A Cloud SQL instance with a public IP | None |
| `constraints/iam.allowedPolicyMemberDomains` | Granting IAM to a principal outside your domain | `roles/iam.policyAdmin` restricts *who* can change policy |
| `constraints/storage.publicAccessPrevention` | Making a bucket publicly readable | `roles/storage.admin` restricts *who* can change access |
| `constraints/bigquery.disableBQOmniAllowedRegions` | BigQuery Omni jobs in disallowed regions | None |

The mechanism difference is the giveaway. IAM says "you cannot call `storage.buckets.delete` on this bucket". Organization Policy says "even if you call `storage.buckets.delete` and you are allowed to, the platform will refuse because a constraint forbids the bucket existing in this state" — no, more precisely: "even if you have permission to create a bucket in `europe-west4`, the platform will reject the creation because the constraint forbids that location."

**The three-way relationship:**

```text
Organization Policy  ->  "is this configuration allowed?"
IAM                  ->  "is this principal allowed to perform this action?"
Both must be satisfied for the action to succeed.
```

An action succeeds only if IAM allows it **and** the organisation policy permits the resulting configuration. Neither can compensate for the other. IAM cannot grant you the right to create a resource that org policy forbids; org policy cannot grant you permission you do not have.

**Inheritance and "policy overrides".** Organization policies inherit downward just like IAM. A constraint set on the organisation applies to every folder, project and resource beneath. And like IAM, you can add a **policy override** at a lower level to relax a constraint — but only if the organisation's policy explicitly allows it. Google's default for most constraints is `ALLOW_OVERRIDE`, meaning a folder or project admin can relax an inherited constraint. Some constraints are `DENY_OVERRIDE` and cannot be relaxed below the point they are set.

The practical difference that catches people: **IAM DENY beats everything; org policy overrides have a different precedence model entirely.** An org policy is not an allow/deny on a permission — it is a filter on a configuration field. You cannot "grant" your way past it with IAM.

**How to see it.** Organization policies are visible in the console under IAM & Admin → Organization Policy, and via `gcloud`:

```bash
gcloud resource-manager org-policies list --project=PROJECT_ID
gcloud resource-manager org-policies describe \
  constraints/gcp.resourceLocations --project=PROJECT_ID \
  --format="yaml"
```

A typical constraint looks like this:

```yaml
constraint:
  displayName: Restrict VM locations
  listConstraint:
    allowedValues:
    - us-central1
    - europe-west4
    - asia-southeast1
  restrictedValues: []
```

### VPC networks

A **Virtual Private Cloud (VPC) network** is a private, software-defined network inside a Google Cloud project. Every Google Cloud resource that needs network connectivity gets an interface in a VPC.

The key structural facts:

- **A VPC network belongs to a project**, and a project has exactly one VPC network in the classic model. Compute Engine instances, Cloud Run services (with VPC egress), GKE nodes, and Private Service Connect endpoints all attach to it.
- **Subnets** divide a VPC network into regional segments. A subnet is regional, not zonal. Subnets let you define IP ranges and the regions they live in.
- **Firewall rules** control traffic between resources and to the internet.
- **A VPC network has its own routing table**, and — importantly — **routes and firewall rules live in the VPC, not in the resource**. This is why a firewall rule can apply to instances in another project if you use Shared VPC.

**Shared VPC** solves the "one VPC per project" problem for enterprises. A host project owns the VPC; service projects attach to it. This lets a central network team own the network topology and firewall rules while application teams own their own projects and resources. The alternative is **VPC peering**, which connects two VPC networks directly (including across organisations) but does not support transitive routing and has more operational complexity.

**Private Google Access** lets resources without public IP addresses reach Google APIs and services — including BigQuery, Cloud Storage and Pub/Sub — without going out to the internet and back. Without it, a Compute Engine instance with no external IP literally cannot run `bq query`.

**Private Service Connect** and **Private Service Access** address a different problem: connecting to a managed service *privately* rather than through its public endpoint. Private Service Connect gives you a private IP to a BigQuery dataset, a Cloud SQL instance or a Memorystore instance. For a data engineer, Private Service Connect matters when a client requires that data never traverses the public internet — Chapter 2.8 covers compliance and residency in depth.

**Serverless networking** deserves a note because it surprises people. Cloud Run and Cloud Run functions by default *do not* use a VPC — outgoing traffic goes directly to the internet through Google-managed infrastructure, and ingress comes from the public internet. Attaching a VPC connector is opt-in. Many people believe serverless workloads are "in the VPC" and are wrong.

### Firewall rules

A firewall rule has three ingredients:

- **Direction**: `INGRESS` (into a resource) or `EGRESS` (out of a resource).
- **Target**: which instances the rule applies to, via a **network tag**.
- **Action**: `allow`, `deny`, or `log`.

Plus the match criteria: source or destination ranges, protocols and ports.

**The default state is deny-all for ingress.** Every VPC network has an implied rule that denies all inbound traffic and allows all outbound. You add `allow` rules; nothing else is needed to lock things down. This is the opposite of many on-premises firewalls, which have a default-allow policy.

**Priority ordering.** Rules are evaluated by priority number, lowest first. The first rule that matches wins. This is how you build an explicit-deny carve-out: a `deny` rule at priority 100 beats an `allow` rule at priority 1000, regardless of how specific the allow rule is.

```text
Priority 100:  deny   tcp:22   from 10.0.0.0/8      to tag:web   -> explicit deny
Priority 1000: allow  tcp:22   from 35.199.0.0/16    to tag:web   -> IAP tunnel
Priority 1000: allow  tcp:443  from 0.0.0.0/0        to tag:web   -> public https
Priority 65535: deny   all      from 0.0.0.0/0        to tag:web   -> implied default
```

**Tags** are the targeting mechanism. An instance with the tag `web` is affected by every rule that targets `tag:web`. This is why you should never target `0.0.0.0/0` at a tag that other instances also carry — one misapplied rule exposes every instance with that tag.

**Firewall rules are not free, and the log action costs money.** Every rule that logs traffic generates log entries that flow into Cloud Logging, which bills by volume. A broad `allow tcp` with `log` on a busy port is a surprisingly common source of surprise bills.

**The default-allow mistake.** `allow tcp:22 from 0.0.0.0/0` exposes SSH to the entire internet. Even if your key is unguessable, the instance is being scanned continuously, and any auth misconfiguration becomes a breach. The correct answers are **IAP TCP forwarding** (SSH through Google's identity-aware proxy, no public IP needed) or a bastion host.

### The compute family

This is the map. Every service below answers the same question — "where does my code run?" — at a different level of abstraction.

#### Compute Engine (IaaS)

You get a virtual machine. You control the guest OS, the packages, the process supervisor, the firewall configuration, the disk layout, and the patching cadence.

Mechanically: a Compute Engine instance is a virtual machine backed by a persistent disk, attached to a VPC network with one or more network interfaces, reachable through firewall rules, given an IAM identity (a service account), and billed per vCPU-hour plus disk plus any attached resources (load balancer, static IP, egress).

```bash
gcloud compute instances create worker-1 \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --subnet=default \
  --tags=data-worker \
  --service-account=dp-worker@PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --boot-disk-size=100GB
```

**When to use it**: you need a specific OS, a specific kernel, a GPU, a legacy application, or a software you cannot containerise. **When not to**: it is the most operationally expensive option and almost always the wrong default for a data pipeline.

**Machine types**: `e2-*` are the cost-optimised general purpose family (`e2-micro` is the free-tier one), `n2-*` are the general purpose workhorses, `c2-*` are compute-optimised, `m2-*` are memory-optimised, `n1-*` are the older broadwell-based family. Custom machine types (`e2-custom-4-8192`) let you pick vCPU and memory independently when a workload is memory-bound.

**Spot VMs** are discounted preemptible capacity — up to 91% off — that can be reclaimed with 30 seconds' notice. For batch data processing they are a large cost win *if* your job is checkpointable. If it is not, a preemption in the middle of an hour-long shuffle costs you the whole hour.

#### App Engine (PaaS)

You deploy source code; Google manages the runtime, the instances, the scaling and the load balancing. It is the oldest serverless-ish PaaS on GCP and its standard and flexible environments differ significantly:

- **Standard environment**: a restricted runtime (Python, Java, Node, Go, PHP, Ruby) with prescriptive sandbox restrictions. Deploys are fast, scale to zero, and cost per instance-hour.
- **Flexible environment**: runs your code in a Docker container on a VM, with more freedom (any runtime, custom binaries, larger instance types) at the cost of more control over scaling and a slower deploy.

App Engine is genuinely good for a stateless HTTP API with unpredictable traffic. It is a poor fit for data engineering: no long-running jobs, awkward access to the network, and a fundamentally request/response programming model.

#### Google Kubernetes Engine (GKE)

Managed Kubernetes. Google runs the control plane (the API server, scheduler, controller manager); you run the nodes and the workloads.

The four modes matter:

- **GKE Autopilot**: Google manages the nodes entirely — you submit a workload and Google chooses the node shape, config and upgrades. This is the mode I recommend for most teams, because node management is pure operational overhead for a data team.
- **GKE Standard**: you manage node pools; Autopilot manages everything else.
- **Regional cluster**: one control plane spanning three zones, nodes spread across them. **This should be your default.**
- **Zonal cluster**: control plane and nodes in one zone. A zonal outage takes the whole cluster down. It is a legacy choice and the source of a well-known class of outage.

GKE gives you portability (upstream Kubernetes), a rich ecosystem (operators, Helm, service meshes), and workload-type flexibility. It costs a management fee (about $0.10 per cluster-node-hour in this course's price model) on top of the node compute.

**GKE for data workloads** is a legitimate choice: running a Spark operator, an Argo workflow, or a Kafka connector set on GKE gives you fine control over pod resources, autoscaling and networking. It is *not* the right choice for a simple scheduled batch job — you would be operating a Kubernetes control plane to run something Dataproc Serverless or a BigQuery scheduled query would do for less money and less effort.

#### Cloud Run (serverless containers)

You push a container image; Google runs it in a container, scales the number of instances with traffic, and bills per request and per resource consumption.

Key mechanics:

- **Requests**, not instances, are the scaling unit. A service can scale to zero when idle.
- **Concurrency** controls how many requests one instance handles simultaneously (default 80).
- **CPU is only allocated during request processing** by default — this is a real cost lever. Set `"cpuAlwaysAllocated": true` if you have background work (or a sidecar) that must run regardless of traffic, and you pay for it continuously.
- **Minimum and maximum instance counts** trade latency against cost. `min-instances: 1` eliminates cold starts at the price of a always-running instance.
- **Billing is per request plus per CPU-second plus per GB-second** of memory — which in this course's model is $0.000024 per CPU-second and $0.0000025 per GB-second, with a generous free tier of 2,000,000 requests, 180,000 vCPU-seconds and 1 GB egress per month.

```bash
gcloud run deploy events-transform \
  --image=REGION-docker.pkg.dev/PROJECT_ID/REPO/events-transform:latest \
  --region=us-central1 \
  --service-account=dp-transform@PROJECT_ID.iam.gserviceaccount.com \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --min-instances=0 \
  --max-instances=50 \
  --concurrency=40 \
  --set-env-vars="PUBSUB_TOPIC=events-normalised,BIGQUERY_DATASET=curated_us-central1"
```

The flags at the bottom are the ones that matter for security: `--no-allow-unauthenticated` and `--ingress=internal-and-cloud-load-balancing` are the difference between an internal service and an internet-facing one. A Cloud Run service that is invoked only by Pub/Sub should have `--ingress=internal-and-cloud-load-balancing`.

#### Cloud Run functions (FaaS)

A single function behind an HTTPS endpoint or an event trigger. You write the handler; Google handles everything else. This is the closest thing GCP has to AWS Lambda or Azure Functions.

```bash
gcloud functions deploy normalise-event \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=functions/normalise_event \
  --entry-point=normalise_event \
  --trigger-topic=events-raw \
  --service-account=dp-transform@PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --memory=512Mi \
  --timeout=120s \
  --min-instances=0 \
  --max-instances=100
```

**The trigger model is the interesting part.** An event-driven function can be triggered by:

- **Pub/Sub** — the natural fit for ingestion and per-message processing.
- **Eventarc** — a unified event bus over many Google services (Cloud Storage object finalisation, Cloud Audit Logs, BigQuery table updates, and 90+ other event types).
- **HTTP** — the default, and the least interesting.
- **Cloud Scheduler** — "run this on a cron schedule". This is how you invoke a function on a schedule.

For data engineering, the Pub/Sub-triggered function is genuinely useful for lightweight per-event transformation: take a message off a topic, validate it, normalise it, write it to BigQuery, done. It scales to thousands of concurrent invocations and costs effectively nothing at low volume. It is the wrong tool for a job that needs to shuffle 10 TB, aggregate over a window, or join against a large dimension table — that is Dataflow's job, and the [Dataflow chapter](22-apache-beam-and-dataflow.md) covers why.

#### Containers and Docker

A container is a process with its own filesystem view, isolated from the host by the kernel's namespaces and cgroups. The image is a layered filesystem plus a configuration. Docker was the tool that made this mainstream; on GCP the container *runtime* is normally containerd, and the tool you use to build and push is one of `docker`, `gcloud builds submit`, or Cloud Build.

The workflow is always the same three steps:

```text
1. BUILD    docker build -t IMAGE:TAG .
2. PUSH    docker push LOCATION-docker.pkg.dev/PROJECT_ID/REPO/IMAGE:TAG
3. RUN     gcloud run deploy ... --image=LOCATION-docker.pkg.dev/PROJECT_ID/REPO/IMAGE:TAG
```

The two rules that matter for a data engineer:

**Reproducibility.** Tag with a git commit SHA, never `latest`, in anything automated. `latest` is a mutable pointer; two deployments of "the same" image can be different binaries, and you cannot roll back to a tag that has moved.

**Build once, run everywhere.** The image that passed your tests is the image you deploy to GKE, Cloud Run and Composer. Rebuilding per environment breaks the guarantee that what you tested is what you ran.

### Artifact Registry

Before you can push a container, you need somewhere to push it. **Artifact Registry** is Google's container and language package registry, and it replaced the older Container Registry.

The naming convention encodes everything:

```text
LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE:TAG
```

- `LOCATION` — the region the registry lives in. Use the same region as the compute that pulls the image, or you pay cross-region traffic on every cold start.
- `PROJECT-ID` — the project that owns the registry.
- `REPOSITORY` — a named repository within the registry. Common practice is one repository per service or per pipeline stage: `events-transform`, `dq-checks`, `ingest-gateway`.
- `IMAGE:TAG` — the image name and tag.

Docker login, then push:

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

gcloud artifacts repositories create events-transform \
  --repository-format=docker \
  --location=us-central1 \
  --description="Event transformation service"

docker build -t us-central1-docker.pkg.dev/PROJECT_ID/events-transform/events-transform:$GIT_SHA .
docker push us-central1-docker.pkg.dev/PROJECT_ID/events-transform/events-transform:$GIT_SHA
```

Artifact Registry also holds Maven, npm, Gradle, Go and Python packages, and it can hold Helm charts. It has one genuinely important feature for data engineering: **Artifact Analysis** scans images for known vulnerabilities and for licences, and it can *block* deployment of images with critical findings — a policy you can enforce with an organization policy constraint (`constraints/artifactregistry.restrictedImages`).

### Choosing a compute option

| Requirement | Choose | Why |
|---|---|---|
| Long-running, stateful, custom OS or GPU | Compute Engine | Nothing else gives you the OS |
| Stateless HTTP API, unpredictable traffic, simple code | App Engine | Zero operations, scales to zero |
| You already run Kubernetes, or need multi-container workloads and operators | GKE | Portability and ecosystem |
| A container with bursty HTTP traffic, want scale-to-zero | Cloud Run | Per-request billing, no nodes |
| A single function behind a trigger, per-event work | Cloud Run functions | Smallest unit, per-invocation billing |
| Scheduled batch over big data | Dataproc / Dataflow / BigQuery jobs | Not a general-purpose compute question |
| GPU or TPU inference | Vertex AI / Compute Engine with GPUs | Managed model serving or raw hardware |

My opinionated default for a data engineer building a new platform in 2026: **use managed services and avoid operating compute entirely unless the workload genuinely requires it.** Specifically:

- BigQuery for analytical queries, with **scheduled queries** or **Dataform** for transformation logic.
- Cloud Run for small HTTP endpoints and event handlers.
- Dataflow for streaming or heavy batch transformation.
- Composer for orchestration.
- GKE only when you have a concrete reason — typically existing Kubernetes expertise, or a need for custom operators, or specialised hardware scheduling.

Operating a Kubernetes cluster is a *job*, not a deployment. A data team that maintains its own GKE cluster has spent its quarter maintaining a cluster.

---

## 🛠️ Hands-On

### Exercise A — Look up the services in the catalogue

```python
"""Inspect the compute services in the course's service catalogue."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from service_catalog import SERVICES, get_service, services_by_category

COMPUTE_IDS = [
    "compute-engine",
    "app-engine",
    "kubernetes-engine",
    "cloud-run",
    "cloud-functions",
]


def main() -> None:
    for service_id in COMPUTE_IDS:
        service = get_service(service_id)
        print(f"{service.name} ({service.id})")
        print(f"  category:     {service.category}")
        print(f"  data role:    {service.data_role}")
        print(f"  pricing:      {service.pricing_model}")
        print(f"  resources:    {', '.join(service.key_resources)}")
        print(f"  available in: {len(service.availability.available)} regions")
        print()

    print("All Compute-category services:")
    for service in services_by_category("Compute"):
        print(f"  {service.name:<26} {service.summary}")


if __name__ == "__main__":
    main()
```

### Exercise B — Compare the cost of the compute options

```python
"""Price the same workload on each compute option."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from cost_model import estimate


def main() -> None:
    # A VM running for 8 hours a day, 30 days.
    vm = estimate("compute-engine", vcpu_hours=2 * 8 * 30, gb_months=100)
    print(vm)
    print()

    # Cloud Run serving 2 million requests with 1 CPU-second each.
    run = estimate("cloud-run", requests=2_000_000, cpu_seconds=2_000_000)
    print(run)
    print()

    # Cloud Run functions: 2 million invocations.
    fn = estimate("cloud-functions", invocations=2_000_000)
    print(fn)


if __name__ == "__main__":
    main()
```

Read the results against the free tier: 2,000,000 Cloud Run requests and 180,000 vCPU-seconds are free every month. The workload above produces 2,000,000 requests (inside the free request allowance) but 2,000,000 CPU-seconds — **more than eleven times the 180,000 free CPU-seconds** — so the bill is $48.00 of CPU time against $19.17 for a VM that is always on. That combination is exactly why Cloud Run's billing model rewards keeping per-request CPU time low: the same 2 million requests handled with 0.05 CPU-seconds each would fall entirely inside the free allowance and cost nothing.

### Exercise C — Create a VPC, a subnet and firewall rules

```bash
# A custom-mode VPC (the default; auto-mode creates subnets for you)
gcloud compute networks create dp-vpc --subnet-mode=custom

# A regional subnet
gcloud compute networks subnets create dp-subnet-us \
  --network=dp-vpc \
  --region=us-central1 \
  --range=10.10.0.0/24 \
  --enable-private-ip-google-access

# Enable the API
gcloud services enable compute.googleapis.com --project PROJECT_ID

# Allow only IAP SSH, never the internet
gcloud compute firewall-rules create allow-iap-ssh \
  --network=dp-vpc \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.199.0.0/16 \
  --target-tags=web

# Deny public SSH explicitly, at a higher priority (lower number) than any allow
gcloud compute firewall-rules create deny-public-ssh \
  --network=dp-vpc \
  --direction=INGRESS \
  --action=DENY \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web \
  --priority=100

# Inspect the effective rules, in evaluation order
gcloud compute firewall-rules list --network=dp-vpc \
  --filter="direction=INGRESS" \
  --format="table(priority, name, action, sourceRanges.list():label=SRC, targetTags.list():label=TAGS, allowed[].map().firewall_rule().list())" \
  --sort-by=priority
```

### Exercise D — Build, push and run a container

```bash
# 1. A minimal service
mkdir -p app && cd app
cat > Dockerfile <<'DOCKER'
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

ENV PORT=8080
CMD ["python", "app.py"]
DOCKER

cat > app.py <<'PY'
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print("request:", fmt % args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
PY

cat > requirements.txt <<'REQ'
REQ

# 2. Create the repository
gcloud artifacts repositories create events-transform \
  --repository-format=docker --location=us-central1

# 3. Authenticate docker to the registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# 4. Build with an immutable tag
export GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local-dev")
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/events-transform/events-transform:$GIT_SHA .

# 5. Push
docker push us-central1-docker.pkg.dev/PROJECT_ID/events-transform/events-transform:$GIT_SHA

# 6. Run it
gcloud run deploy events-transform \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/events-transform/events-transform:$GIT_SHA \
  --region=us-central1 \
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --cpu=1 --memory=512Mi \
  --min-instances=0 --max-instances=10
```

Note the tag is the git SHA, not `latest`. That is the difference between a deploy you can roll back and one you cannot.

### Exercise E — Deploy a Pub/Sub-triggered function

```bash
gcloud functions deploy normalise-event \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=functions/normalise_event \
  --entry-point=normalise_event \
  --trigger-topic=events-raw \
  --service-account=dp-transform@PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --memory=512Mi \
  --timeout=120s \
  --max-instances=50
```

Then check what the function is allowed to do:

```bash
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:dp-transform" \
  --format="table(bindings.role, bindings.members)"
```

A function that writes to BigQuery needs `roles/bigquery.dataEditor` on the dataset and `roles/pubsub.subscriber` on the topic — not on the project.

### Exercise F — See org policy and IAM side by side

```python
"""Contrast the two control systems."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from iam_policy import Binding, Policy, Principal, evaluate

CONSTRAINT = "constraints/gcp.resourceLocations"


def main() -> None:
    policy = Policy()
    owner = Principal("user", "lead@example.com")
    policy.add(owner, Binding("roles/owner"), resource="projects/p")

    decision = evaluate(policy, "lead@example.com", "storage.buckets.create", resource="projects/p")
    print(f"IAM check  -> allowed={decision.allowed}")
    print(f"              {decision.reason}")
    print()

    print("Org policy check (simulated):")
    print(f"  constraint: {CONSTRAINT}")
    print("  allowedValues: ['us-central1', 'europe-west4']")
    print("  action: create bucket in 'asia-southeast1'")
    print("  result: DENIED by constraint, even though IAM allowed the call")
    print()
    print("  The IAM decision stands. The org policy filter rejects the request.")
    print("  Neither can compensate for the other.")


if __name__ == "__main__":
    main()
```

---

## 🛠️ Common Errors and Fixes

### Error 1 — `ERROR: (gcloud.compute.firewall-rules.create) Could not fetch access token` or `Required 'compute.firewalls.create' permission for 'projects/PROJECT_ID'`

**When:** You try to create a firewall rule without the right role.

**Why:** Firewall rules live in the VPC network, and modifying them requires `compute.firewalls.*` on the project that owns the network. In a Shared VPC setup, the **host project** owns the rules — a service project administrator cannot add a firewall rule to a network they use but do not own.

**Fix:** Ask the network team, or grant `roles/compute.networkAdmin` on the host project. If you use Shared VPC, this is the most common friction point in the whole platform.

### Error 2 — `Error: Could not create a firewall rule. Rule with the same name already exists` / `The resource 'projects/PROJECT/global/networks/NETWORK/firewalls/RULE' already exists`

**When:** You re-run a firewall rule creation.

**Why:** Firewall rules are named resources and the name must be unique within the network. The `create` verb fails on an existing name; `gcloud compute firewall-rules create` does not overwrite.

**Fix:** Use `gcloud compute firewall-rules describe` to check, then either update it in place or delete and recreate.

```bash
gcloud compute firewall-rules describe allow-iap-ssh --network=dp-vpc
```

### Error 3 — `ssh: connect to host 34.x.x.x port 22: Connection timed out` after creating an instance

**When:** You cannot reach a freshly created VM.

**Why:** Almost always the firewall. The default ingress rule denies everything, and the "allow SSH" rule created in the console applies only to instances that carry the tag the rule targets. If you did not pass `--tags=web` at creation time, no rule matches it.

**Fix:** Check the instance's tags and the rules that target them.

```bash
gcloud compute instances describe INSTANCE --format="value(tags.items)"
gcloud compute firewall-rules list --network=NETWORK --filter="direction=INGRESS" \
  --format="table(priority, name, action, sourceRanges.list(), targetTags.list())"
```

A close variant is `ERROR: (gcloud.compute.instances.create) Could not fetch key` or `Invalid value for field 'networkInterface.network'` when the project has no `default` network. Every instance needs a network interface; if the default network was deleted you must name one explicitly. Pass `--subnet` or `--network` always — implicit is fine for a human and wrong for a script.

### Error 4 — `ERROR: (gcloud.artifacts.repositories.create) Repository already exists` / `PERMISSION_DENIED: Permission 'artifactregistry.repositories.create' denied`

**When:** You create an Artifact Registry repository.

**Why:** Two causes: the repository name is taken in that project, or the caller lacks `artifactregistry.repositories.create`. Repository names must be unique within their project, and unlike project IDs they *can* be reused after deletion.

**Fix:**

```bash
gcloud artifacts repositories describe REPO --location=us-central1
gcloud artifacts repositories create REPO \
  --repository-format=docker --location=us-central1 \
  --project=PROJECT_ID
```

Grant `roles/artifactregistry.admin` (or `roles/artifactregistry.writer` for pushing only) on the project.

### Error 5 — `unauthorized: authentication required` when pushing to Artifact Registry

**When:** `docker push` fails against `*.docker.pkg.dev`.

**Why:** `docker login` with your user password is not supported. Artifact Registry requires an OAuth token, and the token must be scoped to the registry host.

**Fix:** Use `gcloud auth configure-docker`, which writes the credential helper configuration for you.

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
gcloud auth print-access-token | docker login -u oauth2accesstoken \
  --password-stdin https://us-central1-docker.pkg.dev
```

### Error 6 — `Error: The deploy failed due to an error building the container: ... Read timed out` or `Permission 'artifactregistry.repositories.downloadArtifacts' denied`

**When:** Cloud Run or Cloud Build pulls your image.

**Why:** The runtime service account that pulls the image needs `roles/artifactregistry.reader` on the repository. If you used a custom service account without that role, the deploy fails at the pull step, not at the code step.

**Fix:**

```bash
gcloud artifacts repositories add-iam-policy-binding REPO \
  --location=us-central1 \
  --member="serviceAccount:dp-transform@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"
```

A related symptom is a Cloud Run service that times out on every request at a fixed interval. The default request timeout is 300 seconds, but a **Cloud Run job** defaults to a one-hour timeout and a client that gives up early will look identical. Set both explicitly:

```bash
gcloud run services update events-transform --region=us-central1 --timeout=300s
gcloud run jobs create nightly-aggregate \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/events-transform/aggregate:$GIT_SHA \
  --region=us-central1 --tasks=10 --parallelism=4 --timeout=3600s \
  --service-account=dp-transform@PROJECT_ID.iam.gserviceaccount.com
```

---

## 💡 Production Notes

- **Treat Organization Policy and IAM as two separate checklists in every design review.** Ask: "who is allowed to do this?" and "is this configuration allowed to exist?" A design that answers only the first question is half a design.
- **Never open SSH (or RDP) to `0.0.0.0/0`.** Use IAP TCP forwarding, which gives you identity-aware access with no public IP and a Cloud Audit Log entry per session.
- **Use network tags deliberately and never reuse a tag for unrelated roles.** A tag is the targeting mechanism for every firewall rule; a shared tag means one bad rule exposes many instances.
- **Prefer regional GKE clusters and regional Cloud Run services.** Zonal clusters and single-region buckets are single failure domains and cost you nothing to avoid.
- **Tag container images with the git SHA, never `latest`.** Deploy the same immutable artefact to every environment, and roll back by redeploying the previous digest.
- **Keep Artifact Registry in the same region as the compute that pulls from it.** A cold start that pulls a 500 MB image cross-region is slow and metered.
- **Use `--no-allow-unauthenticated` on every Cloud Run service and function by default.** If a service needs public access, add it deliberately with an Identity-Aware Proxy or load balancer in front, and write down why. Set `min-instances` to 0 for event-driven workloads and 1 where latency matters — every always-on instance is a fixed monthly cost, every cold start is user-visible latency.
- **Set Cloud Run `min-instances` to 0 for event-driven workloads and 1 where latency matters.** Every always-on instance is a fixed monthly cost; every cold start is a user-visible latency.

---

## 🔑 Key Takeaways

- **Organization Policy controls what may exist; IAM controls who may act.** Both must pass. Neither can substitute for the other.
- **Organization policies inherit downward** and can be relaxed below the organisation level via a policy override — unless the constraint is `DENY_OVERRIDE`.
- A **VPC network belongs to a project**; **firewall rules live in the network**, not in the resources. Shared VPC puts the network in a host project owned by a network team.
- **Ingress is deny-by-default.** Rules evaluate by priority, lowest first, first match wins. `deny` at priority 100 beats `allow` at 1000.
- **Network tags are the targeting mechanism**, which makes tag hygiene a security control.
- **Serverless workloads are not in your VPC by default** — Cloud Run and Cloud Run functions egress through Google-managed infrastructure unless you attach a VPC connector.
- The compute ladder: **Compute Engine** (you own the OS) → **App Engine** (source deploy) → **GKE** (managed Kubernetes) → **Cloud Run** (containers, per-request billing) → **Cloud Run functions** (single functions, per-invocation billing).
- **Build once, run everywhere.** The image you tested is the image you deploy; rebuild per environment breaks that guarantee.
- **Artifact Registry is the prerequisite for any container workflow**, and its `LOCATION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG` naming encodes location, ownership and image.

---

## 📚 Practice Exercises

1. Write a one-page comparison of the five compute options for your own team, filling in the decision matrix from this chapter with your real workload characteristics (start-up time, traffic shape, runtime constraints, operational appetite). Circle the one you would pick and defend it in three sentences.
2. Write out, by hand, the complete firewall rule set for a VPC containing a web server, an application server and a database, with no public SSH, HTTPS only to the web tier, and the database reachable only from the app tier. Give every rule a priority number and state the implied default.
3. Explain the difference between "IAM denied it" and "Organization Policy blocked it" for each of these scenarios: creating a bucket in a forbidden region; attaching a serial console to a VM; making a bucket public; deleting a project that has a Shared VPC lien. For each, state which control system is the right one.
4. Using the course's cost model, price: (a) a 4-vCPU VM running 4 hours a day for 30 days with a 200 GB disk; (b) the same workload as a Cloud Run service handling 500,000 requests with 2 CPU-seconds each; (c) the same as Cloud Run functions. Then explain which one wins at this volume and which wins at ten times the volume.
5. Build and push a container to Artifact Registry with a git-SHA tag, deploy it to Cloud Run with `--no-allow-unauthenticated` and `--ingress=internal-and-cloud-load-balancing`, and call it with an identity token. Record the exact commands, then explain what each flag prevents.
6. Deploy a Pub/Sub-triggered Cloud Run function that writes to a BigQuery dataset. Then use `gcloud projects get-iam-policy` to show that the function's service account holds *only* the roles it needs, and explain what each role contributes.
7. Research the difference between the Cloud Run **service** timeout, the Cloud Run **job** timeout and the Pub/Sub **acknowledge deadline**, and explain how they interact when a downstream write fails. Write down the failure mode you would expect.
8. Create a regional GKE cluster with Autopilot and a zonal one with Standard, then compare their node management, upgrade behaviour and failure domains. Argue for one of them as the default for a data team, and name the one workload that would justify the other.

---

## 📖 Further Reading
- [Organization Policy Overview](https://cloud.google.com/resource-manager/docs/organization-policy-overview)
- [Organization Policy Constraints (list of all constraints)](https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints)
- [VPC Networks: Overview](https://cloud.google.com/vpc/docs/overview)
- [Using Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc)
- [Firewall Rules Overview](https://cloud.google.com/vpc/docs/firewalls)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
