# Platform Fundamentals — Interview Questions

## 🎯 How to use this file

Fourteen questions covering the Module 1 material: cloud computing fundamentals, regions and zones, the resource hierarchy, IAM, service accounts, organization policies, networking and compute. Read the question, answer it out loud in the shape the answer demonstrates — direct answer, mechanism, trade-off, production detail — then check yourself against the module. Every question that touches the course's own modules has runnable code at the bottom.

## Questions

### Q1. Why does GCP talk about *regions* and *zones* separately, and what breaks if you ignore the distinction?

**Answer.** A region is a geographic location (like `us-central1`), and a zone is one of the three isolated failure domains inside it (`us-central1-a`, `-b`, `-c`). Zones give you a second copy of a failure domain; regions give you a second copy of a *geography*.

**Mechanism.** Within a region, zones are independent power, cooling and networking, so a zonal outage does not take down the other zones. Between regions, the failure domains are entirely independent — but so is the network path, so cross-region traffic is slower and, on egress, more expensive.

**Trade-off.** Spanning zones costs you latency and complexity (you must handle the fact that a zone going away degrades rather than fails your service). Spanning regions costs you money and a distributed-consistency design. Neither is "free redundancy."

**In practice.** The course models this exactly: every region has three zones, and a resource placed in `us-central1` should be placed in a *region*, not a zone, unless you specifically need zonal isolation. The rule I follow: **replicate stateless compute across zones, replicate stateful systems across zones *and* regions, and put the regional copy close to the user.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import REGIONS, zones_in

print(len(REGIONS), "regions")
print(zones_in("us-central1"))
```

---

### Q2. What is the GCP resource hierarchy, and why does it matter that inheritance flows *downward*?

**Answer.** The hierarchy is organization → folders → projects → resources, and IAM policies are inherited downward: a grant on a folder applies to every project inside it and every resource inside those projects.

**Mechanism.** When GCP evaluates a permission request, it walks the resource's ancestry, collects every applicable binding, and applies the precedence rules — explicit DENY beats any ALLOW, any matching ALLOW beats the default deny. There is no implicit allow; if nothing matches, the call is `PERMISSION_DENIED`.

**Trade-off.** Inheritance is what makes IAM manageable at scale — one folder-level grant covers hundreds of projects. It is also why a badly-scoped grant is catastrophic: there is no "scope" that stops inheritance except a conditional binding or an explicit deny.

**In practice.** The course's `ancestor_paths` function reproduces the step-down rule, and it steps in *type/name pairs*, not single path segments. `"projects/p/buckets/b"` inherits from `"projects/p"` — but there is no such scope as `"projects/p/buckets"`, because that is not a real GCP binding target. Treating it as one makes a policy look like it inherits grants it does not.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import ancestor_paths

print(ancestor_paths("projects/p/buckets/b/objects/o"))
```

---

### Q3. Why does a project-level `roles/owner` binding worry me?

**Answer.** It grants every permission in the project, and because GCP IAM grants inherit *downward*, that includes every bucket, dataset and table underneath — so the blast radius is the whole project, not the one resource you meant to expose.

**Mechanism.** GCP IAM policies are additive down the resource hierarchy: a binding on `projects/p` applies to `projects/p/buckets/b`. There is no scope that stops inheritance except a conditional binding or an explicit deny. `roles/owner` also includes the permission to grant IAM to others, so the holder can widen their own access.

**Trade-off.** `roles/owner` at the project level is convenient and dangerous. `roles/storage.objectViewer` on one bucket is verbose and safe. For a data pipeline, prefer a service account with per-service roles.

**In practice.** I grant `roles/bigquery.dataEditor` on the project and `roles/storage.objectCreator` on the landing bucket — deliberately not `roles/owner`. If a job needs to grant IAM to others, that is a separate service account with `roles/resourcemanager.projectIamAdmin`, and only on the child projects that need it.

**Failure story.** A team gave an analytics contractor `roles/owner` on the project "just for the first week". On day three the contractor's laptop had a leaked token, and the exfiltration path included the production bucket and the BigQuery dataset. The fix was rotating the service-account key and moving to per-resource roles — but the data was already copied.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from platform_sim import build_demo_project

project = build_demo_project()
print(project.can("analytics@example.com", "storage.objects.get",
                  resource="projects/gcp-de-course/buckets/raw-events"))
print(project.can("analytics@example.com", "storage.objects.create",
                  resource="projects/gcp-de-course/buckets/raw-events"))
```

---

### Q4. What are the three service-account questions you must answer before wiring one into a pipeline?

**Answer.** *Who is it?* (which service account, and what is it allowed to do), *how does it authenticate?* (workload identity, not a downloaded JSON key), and *what happens to the audit trail?* (which principal shows up in Cloud Logging).

**Mechanism.** A service account is an identity with an email address ending in `.iam.gserviceaccount.com`. It is not a login — it cannot sign in to the console. It acts only by being *impersonated* or *attached* to a workload, and the attaching mechanism determines the authentication story: a key file, an attached service account (Cloud Run, GKE, GCE), or Workload Identity Federation (external CI, Kubernetes).

**Trade-off.** Keys are portable and simple, and they are also a long-lived secret that can be exfiltrated and replayed from anywhere. Workload Identity removes the secret entirely and gives you short-lived tokens, at the cost of some setup and a dependency on the CI provider's OIDC support.

**In practice.** The rule I give every new engineer: **no JSON keys in a repository, ever.** For GKE, use Workload Identity Federation with a Kubernetes Service Account bound via IAM. For GitHub Actions, use the Workload Identity Federation provider with a dedicated pool. Keys only appear as a last resort, in Secret Manager, with rotation.

**Failure story.** A Dataflow job held a JSON key in a Terraform state file in a bucket that a developer had made world-readable for debugging. The key was valid for 365 days because nobody set an expiry. The remediation bill included rotating the key, auditing every resource that identity touched, and a postmortem whose root cause was "one key, one year, one readable bucket".

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from platform_sim import build_demo_project

project = build_demo_project()
for line in project.explain("pipeline-sa@gcp-de-course.iam.gserviceaccount.com"):
    print(line)
```

---

### Q5. What is the difference between a permission, a role and a policy, and which do you actually grant?

**Answer.** A permission is the atomic verb (`storage.objects.get`). A role is a named bundle of permissions. A policy is the set of bindings attached to a resource. You grant **roles**; GCP resolves each role to its permissions at evaluation time.

**Mechanism.** GCP has three kinds of role. **Primitive** roles (`roles/owner`, `roles/editor`, `roles/viewer`) grant permissions across every resource type in the project, including ones that did not exist when the role was defined. **Predefined** roles are service-specific and granular (`roles/storage.objectViewer`, `roles/bigquery.jobUser`). **Custom** roles list exactly the permissions you want.

**Trade-off.** Primitive roles are one click and impossible to review. Predefined roles are the default choice and slightly verbose. Custom roles are precise but they are real code — they need review, they need versioning, and a typo in a permission name silently grants nothing.

**In practice.** The decision rule: predefined role close enough → use it; nothing fits → custom role; nothing fits and it is temporary → primitive role with a written expiry date. The course encodes 23 roles, and `roles/bigquery.jobUser` is the one people miss — it lets you *run* queries without being able to *read* the data, which is exactly right for a CI job that only needs to execute a test query.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import ROLES, ROLE_SUMMARY

print(len(ROLES), "roles modelled")
for name in ("roles/bigquery.jobUser", "roles/bigquery.dataViewer"):
    print(name, "->", len(ROLES[name]), "permissions")
    print("   ", ROLE_SUMMARY[name])
```

---

### Q6. Explain the IAM evaluation order, including what happens when a conditional binding does not match.

**Answer.** GCP collects all bindings applicable to the resource, discards those whose principal does not match and those whose condition is not satisfied, then applies: explicit DENY wins over everything, any matching ALLOW wins, otherwise deny by default.

**Mechanism.** The precedence is evaluated **after** collection, not per-level. A DENY at the bucket level overrides an ALLOW inherited from the project. Conditions are evaluated against the request's attributes — typically resource tags or IAM Conditions with CEL — and a binding whose condition is not satisfied simply *does not apply*; it is discarded rather than treated as a deny.

**Trade-off.** The fail-closed default is right for a security system, and it does produce the most common support ticket: a user with a correct role still gets `PERMISSION_DENIED`. The fix is nearly always a missing condition attribute or a group membership, not a missing role.

**In practice.** The course's `evaluate()` returns a `Decision` carrying `allowed`, `reason`, `matched_roles`, `denied_roles` and `inherited` — that last field tells you whether the decisive grant came from the resource itself or from an ancestor, which is the difference between "their role is wrong" and "their role is right but attached at the wrong level". Use `explain_principal()` to answer "why can I do this?".

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import Binding, Policy, Principal, evaluate

policy = Policy()
policy.add(Principal("user", "ana@example.com"), Binding("roles/storage.objectViewer"))
policy.add(Principal("user", "ana@example.com"),
           Binding("roles/storage.objectViewer", condition="env == prod"))

print(evaluate(policy, "ana@example.com", "storage.objects.get").allowed)
print(evaluate(policy, "ana@example.com", "storage.objects.get",
               attributes={"env": "prod"}).allowed)
```

---

### Q7. Why does the blast radius of a grant matter, and how do you actually measure it?

**Answer.** Blast radius is the set of resources a compromised identity can reach. Because IAM inherits downward, a single grant can cover hundreds of resources you never enumerated, so you cannot reason about it from the grant alone — you have to measure it.

**Mechanism.** `blast_radius(policy, identity, resources)` walks each candidate resource, computes the identity's effective permissions there, and reports whether the set is non-empty. The subtlety is that "can reach" is not binary in the real world — `roles/storage.objectCreator` lets you write but not read, and a writer can still corrupt data.

**Trade-off.** Reducing blast radius means more bindings, more maintenance, and more `PermissionDenied` errors from misconfiguration. Accepting a large blast radius means faster onboarding and faster incidents.

**In practice.** I run the blast-radius question against every IAM change: *if this key leaked tonight, what could an attacker read, write or delete?* The answer has to be a list of resources, not a feeling. That list then defines the monitoring — access logs, audit logs, and a budget alert on the resources in it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import Binding, Policy, Principal, blast_radius

policy = Policy()
policy.add(Principal("serviceAccount", "sa@p.iam.gserviceaccount.com"),
           Binding("roles/storage.objectCreator"))

resources = [
    "projects/p",
    "projects/p/buckets/raw",
    "projects/p/buckets/curated",
    "projects/p/datasets/sales",
]
for resource, reachable in blast_radius(
        policy, "sa@p.iam.gserviceaccount.com", resources).items():
    print(reachable, resource)
```

---

### Q8. When would you use a conditional binding, and what happens when the condition fails?

**Answer.** A conditional binding grants a role only when the request's attributes satisfy a condition — typically a resource tag like `environment=prod`. If the condition does not match, the binding simply does not apply and the request falls through to the next binding, ultimately denying.

**Mechanism.** Conditions are evaluated against attributes on the resource being accessed, not on the principal. A common pattern is: grant `roles/bigquery.dataViewer` where `access_tier == gold`, and grant nothing otherwise. The IAM Conditions engine uses CEL, and the evaluation happens *after* collection of applicable bindings.

**Trade-off.** Conditions give you fine-grained, self-documenting access that changes with a tag update rather than a role update. They also make debugging harder: a permission failure now has two possible causes (the role or the condition), and the error message does not usually say which.

**In practice.** The course's condition syntax is simplified — comma-separated `attribute == value` pairs — and it **fails closed**: a clause with no `==` returns False, and a missing attribute returns False. That is the correct behaviour for a security control, and it is the one thing to get right if you write your own.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import Binding, Policy, Principal, evaluate

policy = Policy()
policy.add(Principal("user", "ana@example.com"),
           Binding("roles/storage.objectViewer", condition="env == prod"))

print(evaluate(policy, "ana@example.com", "storage.objects.get",
               attributes={"env": "dev"}).reason)
```

---

### Q9. What is an organization policy, and how does it differ from IAM?

**Answer.** An organization policy is a *constraint on configuration*, not a grant of access. It says "nobody may create a bucket in this location" or "every bucket must be uniform-access with public access prevention on". IAM says who may do what; org policy says what configurations are allowed at all.

**Mechanism.** Org policies live at the organization or folder level and cascade downward to projects, exactly like IAM bindings. They are **not** inherited in the same way and they are not principal-specific: they apply to everyone, including the org admin, unless an explicit exemption is granted. Custom constraints use CEL expressions against resource attributes.

**Trade-off.** Org policies are the right tool for guardrails that must hold regardless of who is asking, and they are the only way to enforce things IAM fundamentally cannot express — "no external IPs", "no public buckets", "no resources in `europe-west2`". The cost is that they can break automation silently, and a mis-scoped constraint can block your own pipelines.

**In practice.** The one every data engineer should set up on day one is `constraints/gcp.resourceLocations` — because a misconfigured default region can place a bucket containing EU customer data in `us-central1`, and that is a residency breach you cannot undo after the fact. Set it on the folder, scoped to the regions your compliance team approved.

**Failure story.** A team enabled `constraints/gcp.restrictNonConfidentialComputing` on a folder that held their Dataproc clusters. The clusters were Confidential Computing-enabled by default for a security review, and the policy blocked every cluster creation. The pipeline stopped for two days while the exemption was filed — which is the real lesson: constraints need an exception process and a rollout in "list" mode before "enforce".

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import ROLE_SUMMARY

print(ROLE_SUMMARY["roles/orgpolicy.policyAdmin"])
print(ROLE_SUMMARY["roles/resourcemanager.projectIamAdmin"])
```

---

### Q10. Walk me through GCP's VPC networking for a data pipeline. What are the pieces that actually matter?

**Answer.** A VPC is a private network with a CIDR range, subnets in regions, firewall rules, routes, and optionally Cloud NAT and a private service connection. For a data pipeline the pieces that matter are: **Private Google Access** (so VMs can reach Google APIs without public IPs), **VPC peering or Shared VPC** (to connect to on-prem or other projects), and **Private Service Connect / Private Service Access** (to give managed services a private IP).

**Mechanism.** GCP's default route `default-internet-gateway` sends non-matching traffic to the internet. Private Google Access routes `199.36.153.8/30` and `199.36.153.4/30` (plus IPv6 equivalents) to Google's network, so a VM with no public IP can still reach `bigquery.googleapis.com`. Firewall rules are stateful and evaluated by priority; the default deny-in-all rules mean unmatched ingress is dropped.

**Trade-off.** Private networking reduces attack surface and removes NAT egress cost, but it makes on-call debugging harder — you cannot curl an external endpoint from a private VM. Shared VPC gives central network administration across projects but requires the `roles/compute.networkAdmin` on the host project and careful subnet sharing.

**In practice.** I give every data project its own VPC with Private Google Access on, one subnet per region, and a `deny-all` ingress rule above a rule that allows only the dataflow worker ranges. Cloud Storage and BigQuery endpoints get access through Private Service Connect rather than `Private Google Access`, because those are the two paths that handle `storage.googleapis.com` correctly.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("compute-engine", "kubernetes-engine", "cloud-run", "dataflow"):
    service = SERVICES[service_id]
    print(f"{service.name:<20} {service.key_resources}")
```

---

### Q11. When would you choose Compute Engine, GKE, Cloud Run or Cloud Functions for a data workload?

**Answer.** Compute Engine when you need a persistent, custom-configured machine or a specific OS-level dependency. GKE when you need a scheduler, operators, or a multi-container platform with your own scheduling policy. Cloud Run when the workload is a container triggered by an event or HTTP request and scales to zero. Cloud Functions when the workload is a single function behind a trigger and you want no container build at all.

**Mechanism.** The four differ in the unit of deployment and the scaling model. Compute Engine scales by instance groups and you own the OS. GKE gives you a scheduler (the kube-scheduler) and a container orchestrator with self-healing and horizontal autoscaling on custom metrics. Cloud Run scales on request concurrency and bills by CPU-second and GB-second. Cloud Functions bills per invocation.

**Trade-off.** Serverless is cheaper when idle and more expensive under sustained load with a minimum-instance floor; a Dataflow streaming job at 24/7 is cheaper on Dataflow than on Cloud Run because you can size it to the workload. GKE adds an operational tax — you now own node upgrades, autoscaler tuning and cluster version skew.

**In practice.** The course's rule of thumb: batch transform → Dataproc or Dataflow batch; streaming → Dataflow streaming; glue orchestration → Composer or Workflows; a one-off HTTP-triggered data API → Cloud Run. Only reach for GKE when you genuinely need custom scheduling or a sidecar that the managed platforms cannot give you.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

run = estimate("cloud-run", requests=1_000_000, cpu_seconds=60_000, apply_free_tier=False)
print(run)
```

---

### Q12. How do you pick a region for a data platform, and what does it cost you to get it wrong?

**Answer.** Pick the region closest to your *users and your data*, then check that every service you need is generally available there. Multi-region for the landing zone when you need global reads; single region for compute when latency to the data matters.

**Mechanism.** GCP locations have a hierarchy: multi-region (`us`, `eu`) → region (`us-central1`) → zone. A resource's location determines which region its jobs run in, and cross-region access is what triggers egress charges and the latency hit. Not every service is available everywhere — the course's catalog records availability, preview and restricted status per region precisely because "just pick a region" fails in practice.

**Trade-off.** A multi-region bucket gives durable global reads at a slightly higher storage price and no write locality guarantees — two simultaneous writes in different regions can conflict. A single region is cheaper and simpler but makes every other region a remote region.

**In practice.** The course's `nearest_region` function is a simplification, but the *shape* of its answer is the point: a service is never truly unavailable, it is available elsewhere at a latency and a data-residency cost. Before you commit, check `services_available_in(region)` against your required service list.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import REGIONS, SERVICES, services_available_in

print(len(services_available_in("us-central1")), "services in us-central1")
print(len(services_available_in("southamerica-east1")), "services in southamerica-east1")
for name in ("biglake", "datastream", "dataplex", "memorystore"):
    service = SERVICES[name]
    print(f"{service.name:<24} preview={service.availability.preview} "
          f"restricted={service.availability.restricted}")
```

---

### Q13. Explain "no downward inheritance" for IAM — and when a binding *does* apply to a child resource.

**Answer.** IAM bindings are inherited downward from ancestors, but each service defines its own resource tree, and the hierarchy steps in *type/name pairs*. A binding on `projects/p` applies to `projects/p/buckets/b`; there is no scope for "the buckets of project p" that is separate from the project itself.

**Mechanism.** The resource path is a sequence of pairs: `projects/p`, `buckets/b`, `objects/o`. Walking up the ancestry means dropping the last pair at a time. `projects/p/buckets/b/objects/o` → `projects/p/buckets/b` → `projects/p`. Note what is *not* in that list: `projects/p/buckets/b/objects` and `projects/p/buckets`. Treating those as scopes is the single most common mistake in hand-rolled IAM tooling.

**Trade-off.** The real platform has additional scopes — Google Groups, service accounts as members, and per-service permissions with service-specific resource paths — but the pair-stepping rule is the backbone, and it is what you implement when you build a policy linter.

**In practice.** When I write a policy-linting tool, the first thing it checks is that every binding's resource path is a *real* GCP scope, and the second is that a project-level grant does not silently cover a bucket the team believes is isolated.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import ancestor_paths

for path in ("projects/p", "projects/p/buckets/b", "projects/p/buckets/b/objects/o"):
    print(path, "->", ancestor_paths(path))
```

---

### Q14. How do you propose a data processing strategy when the interviewer gives you an under-specified problem?

**Answer.** Start from the *shape of the data*, not the brand of the service. Latency requirement, volume, update pattern, query pattern and consistency requirement determine the architecture; only then do you pick the GCP service.

**Mechanism.** The decision axes are: **volume** (does it fit in a warehouse table, a wide-column store, or a distributed file system), **latency** (batch hours → Dataflow batch/Dataproc; minutes → Composer; seconds → Dataflow streaming; sub-second → Cloud Spanner), **query pattern** (analytical scans → BigQuery; point lookups by key → Firestore/Datastore/Bigtable; range scans on time-series → Bigtable), and **consistency** (strong → Spanner; eventual → everything else).

**Trade-off.** Every service you add is another thing to secure, monitor, upgrade and pay for. A pipeline that uses four services has four IAM policies, four cost centres and four failure modes.

**In practice.** My proposal template is one page: source → landing → processing → serving, with the service chosen at each arrow and the reason stated in one sentence. Then the hardening: the idempotency key, the retry semantics, the dead-letter path, the cost driver. The course's pipeline maps one-to-one onto this: ingest (Pub/Sub), validate (a `DoFn`), publish (Pub/Sub), load (BigQuery partitioned table), with a deterministic `partition:event_id` identity so a retry is safe.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, partition_for_date

partition = partition_for_date("2026-01-15")
print("partition decorator:", partition)
print("idempotency key:", dedup_key("evt-0001", partition))
```

---

## 📚 Related chapters

- [1.1 — Introduction to Cloud Computing](../chapters/01-introduction-to-cloud-computing.md)
- [1.2 — Regions, Zones & the Resource Hierarchy](../chapters/02-regions-zones-and-resource-hierarchy.md)
- [1.3 — Identity & Access Management](../chapters/03-identity-and-access-management.md)
- [1.4 — Organization Policies, Networking & Compute](../chapters/04-org-policies-networking-and-compute.md)
- [1.5 — Proposing a Data Processing Strategy](../chapters/05-proposing-a-data-processing-strategy.md)

## 📖 Further Reading

- [Resource hierarchy overview](https://cloud.google.com/resource-hierarchy/docs/overview)
- [IAM overview and evaluation order](https://cloud.google.com/iam/docs/overview)
- [IAM Conditions overview](https://cloud.google.com/iam/docs/conditions-overview)
- [Organization policies overview](https://cloud.google.com/resource-manager/docs/organization-policy-overview)
- [GCP locations and regions](https://cloud.google.com/about/locations)
