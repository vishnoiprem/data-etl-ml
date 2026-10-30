# 1.3 — Identity & Access Management

> **Section 1 · GCP Fundamentals · Lecture 1.3 · 8:00**

## 🎯 What you will learn
- The four identity types in GCP and when each one is the right thing to grant
- The difference between a **permission**, a **role** and a **policy**
- Primitive roles versus predefined roles versus custom roles — and when each is correct
- How to actually assign a role, and where the grant should be attached
- The three service-account identity questions every engineer must answer before wiring one up
- Least privilege as a workflow, not a slogan
- Conditional bindings, and why they fail closed
- The blast-radius question: what breaks if this identity is compromised

---

## 🧠 Concept

### IAM is a policy evaluation engine, not a list of checkboxes

GCP's IAM answers one question: *may this principal perform this permission on this resource, right now, given these attributes?* Everything else — roles, groups, service accounts, conditions, deny policies — is a way of writing down the answer more concisely than listing every permission individually.

The evaluation order, in the real platform:

1. Collect every applicable binding by walking the resource hierarchy from the resource up to the organization.
2. Discard bindings whose principal does not match the caller (directly, through a group, or through a domain).
3. Discard bindings whose **condition** is not satisfied by the request's attributes.
4. If any remaining binding is an **explicit DENY** containing the permission → **deny**. This wins over everything, at any level of the hierarchy.
5. Otherwise, if any remaining binding is an **ALLOW** whose role contains the permission → **allow**.
6. Otherwise → **deny by default**.

Step 6 is the one people forget. **There is no implicit allow.** If no binding grants the permission, the call fails with `PERMISSION_DENIED`. This is fail-closed, which is the correct default for a security system.

The course's `iam_policy` module implements exactly this order, and the `Decision` it returns carries `allowed`, `reason`, `matched_roles`, `denied_roles` and `inherited` — the last field tells you whether the decisive grant came from the resource itself or from an ancestor.

### The four identity types

GCP recognises exactly four kinds of principal. Choosing the right one is more than half of access design.

| Type | Canonical form | Created by | Lifetime | Typical use |
|---|---|---|---|---|
| **User** | `user:ana@example.com` | Your identity provider | Human's tenure | A named engineer, analyst or approver |
| **Group** | `group:data-eng@example.com` | Google Workspace / Cloud Identity | Membership-driven | Team access, reviewed centrally |
| **Service account** | `serviceAccount:sa@p.iam.gserviceaccount.com` | `gcloud iam service-accounts create` | Application lifetime | Any non-human workload |
| **Domain** | `domain:example.com` | Cloud Identity | Permanent | Broad, coarse grants to a whole org |

**Users** map to a human being. Granting a role to a user directly is fine for a prototype and bad for production: when the person leaves, the grant stays, and when they change teams, the grant does not move with them.

**Groups** are the production answer for humans. Bind the group to the role, manage membership in the identity provider. Group membership changes are auditable and instantaneous. A group is also the right unit for *approval workflows* — the group `data-release-approvers` can be granted a role that unlocks a production deployment, and only that group can approve.

**Service accounts** are non-human identities with keys, tokens and an email address. Every automated workload needs one: a Dataflow job, a Composer DAG's worker, a Cloud Run service, a Cloud Build pipeline, a GKE node's kubelet identity. Chapter 1.3's central section is about using them correctly.

**Domains** grant to everyone in a domain, present and future. Use them sparingly — `domain:example.com` on `roles/storage.objectViewer` is a blunt instrument that quietly grants every future hire access to everything you stored. Domains also do **not** apply to service accounts, which is often the surprising part.

### Permissions, roles, policies

**A permission** is the atomic verb, like `storage.objects.get` or `bigquery.tables.getData`. GCP has thousands. Permissions are grouped into roles.

**A role** is a named bundle of permissions. Roles are what you grant. There are three kinds:

**Primitive roles** are the old ones: `roles/owner`, `roles/editor`, `roles/viewer`. They are broad, they cover resource types that did not exist when they were defined, and — critically — they grant permissions across *all* resource types in the project.

**Predefined roles** are service-specific and granular: `roles/storage.objectViewer`, `roles/storage.objectCreator`, `roles/bigquery.dataViewer`, `roles/bigquery.jobUser`, `roles/pubsub.publisher`, `roles/pubsub.subscriber`. These are the roles you should reach for by default.

**Custom roles** are ones you define, listing the exact permissions you want. They are useful when no predefined role is close enough — a role with "read the bucket and write objects but not delete or change ACLs" is often exactly what an ingestion service needs.

The decision rule I use:

```text
Predefined role that is close enough?  -> use it
No predefined role fits?              -> custom role
Nothing fits and it is temporary?     -> primitive role + a deadline
```

**A policy** is the set of bindings attached to a resource. `gcloud projects get-iam-policy` returns one.

### Roles in detail: the surprising ones

The course project encodes 23 roles with their exact permission sets. Several deserve explicit attention because their behaviour surprises people.

**`roles/storage.objectViewer`** grants `storage.objects.get`, `storage.objects.list` and `storage.buckets.get`. Read the objects, list them, and see the bucket's metadata. It does **not** grant `storage.objects.create` — the ingestion service that creates objects needs a different role.

**`roles/storage.objectCreator`** grants `storage.objects.create` and `storage.buckets.get`. It creates objects but **cannot read them**. This is the classic "why can my pipeline write to the bucket but not read from it" answer, and it is exactly how the demo project is configured: `pipeline-sa` has `roles/storage.objectCreator` and can write raw events, but the analyst has `roles/storage.objectViewer` and can read them. The two roles are deliberately not interchangeable, and combining them into `roles/storage.admin` would let the pipeline read the data it produced — which for a one-way landing zone is unnecessary.

**`roles/bigquery.dataViewer`** grants `bigquery.datasets.get`, `bigquery.tables.get`, `bigquery.tables.getData` and `bigquery.jobs.createQuery`. It lets you read table data and run queries. It does **not** grant `bigquery.tables.create` — you cannot create tables. Note that it *does* grant `createQuery`, which is the permission that lets an analyst run a query against the table. This is why "the analyst can see the data" and "the analyst can create a new table" are independent decisions.

**`roles/bigquery.jobUser`** grants `bigquery.jobs.create`, `bigquery.jobs.createQuery` and `bigquery.datasets.get` — but not `bigquery.tables.getData`. This is the role for a service that needs to *run queries* without being able to *read the results*. It is the classic analyst-sandbox pattern: users can run queries, but the query results and the underlying data stay invisible to them. Useful in a shared analytics project where you want to let people experiment without exposing row-level data.

**`roles/owner`** grants every permission, including `resourcemanager.projects.setIamPolicy` — the permission that lets the holder change who else has access. **A project-level `roles/owner` can grant itself to anyone.** It is the role you hand to one or two people during setup and then take away.

**`roles/editor`** grants broad read/write across most resources but explicitly **not** `resourcemanager.projects.setIamPolicy` and not `iam.serviceAccounts.*` in the course model. Editor cannot change the IAM policy, and cannot act as service accounts. This is a real and useful distinction: editor is the right role for a team that needs to create and manage resources but should not be able to escalate privilege.

The course's `--iam` command shows the whole thing at once:

```text
  ✓ analytics@example.com                              storage.objects.get
  ✗ analytics@example.com                              storage.objects.create
  ✓ analytics@example.com                              bigquery.tables.getData
  ✓ analytics@example.com                              bigquery.tables.create
  ✓ pipeline-sa@gcp-de-course.iam.gserviceaccount.com  pubsub.topics.publish
  ✓ pipeline-sa@gcp-de-course.iam.gserviceaccount.com  pubsub.subscriptions.consume
  ✗ stranger@example.com                               storage.objects.get
```

The `✗` lines are the pedagogy: same project, same policy, different answers because different identities have different bindings — and because a binding on one resource does not automatically grant on another.

### The three service-account identity questions

Every time you attach a service account to a workload, answer these three questions in order. If you cannot answer all three, do not attach it yet.

**Question 1 — Who is this identity?**

A service account is not a human. It has no owner, no manager, no password and no expiry. It persists until someone deletes it. That means a service account created "for the pipeline" in 2024 is still there in 2026, still holding whatever roles it accumulated, and nobody remembers granting it. Give every service account a name that says what it does (`dp-landing-writer`, not `sa-1`), and keep an inventory.

**Question 2 — Who can impersonate it?**

Any principal with `iam.serviceAccounts.actAs` on the service account can make API calls *as* that service account — meaning they get its permissions, not their own. This is the most abused permission in GCP, because it is easy to grant and completely invisible in the resource's own IAM list.

The relevant roles:

- `roles/iam.serviceAccountUser` — `iam.serviceAccounts.actAs` only. Grant this to a human who needs to deploy as the service account.
- `roles/iam.serviceAccountAdmin` — create, get and act as service accounts. Broader; avoid at project scope.
- `roles/iam.serviceAccountViewer` — read metadata only.

The correct pattern: grant `roles/iam.serviceAccountUser` **on the specific service account**, not `roles/iam.serviceAccountAdmin` on the project. And never grant `roles/owner` to a human just so they can deploy — `roles/owner` at project scope includes `iam.serviceAccounts.actAs` for every account in it.

**Question 3 — What is the blast radius?**

If this service account's key leaks, what can the attacker do? Answer it in terms of resources, not verbs: "it can read and delete every object in the `raw-events` bucket", "it can modify any table in the `curated` dataset", "it can publish to any topic in the project".

This is the question that makes least privilege concrete. A service account with project-level `roles/bigquery.dataEditor` has a blast radius of *every table in every dataset in the project*, whether or not the pipeline touches them. The same job scoped to `projects/p/datasets/curated` has a blast radius of one dataset.

A useful rule of thumb: **if you cannot state the blast radius in one sentence without naming resources, your role is too broad.**

### Least privilege as a workflow

"Least privilege" is usually presented as a virtue. It is more useful as a process:

1. **Start from the code.** Read what the workload actually calls. `gsutil cp` needs `storage.objects.create`. `bq query` needs `bigquery.jobs.createQuery`. A Dataflow job reading GCS and writing BigQuery needs `storage.objects.get` on the bucket and `bigquery.tables.update` on the dataset — plus `bigquery.jobs.create`.
2. **Grant at the resource, not the project.** Attach the binding to the bucket, dataset or topic the job uses.
3. **Prefer the narrowest predefined role that includes the needed permission.** `roles/storage.objectViewer` over `roles/storage.admin`.
4. **Split by phase when the roles conflict.** An ingestion service that only writes should not also read. Two service accounts — a writer and a reader — is a real and cheap design, and it is how the demo project is built.
5. **Re-review on a schedule.** Roles accumulate. `gcloud projects get-iam-policy` diffed against last quarter's snapshot is a genuinely useful quarterly ritual.

There is a legitimate counter-argument I will make: **over-granting a role to a service account inside a narrowly scoped project, in a sandbox, is cheaper in engineering time than a precise policy that breaks a scheduled job at 3 a.m.** The trade-off is real. The answer is not "always least privilege" — it is "least privilege by default, with a documented, expiring exception for non-production".

### Conditional bindings

A conditional binding applies only when a condition expression is satisfied. Conditions are evaluated against **attributes** of the request: resource labels, the principal's attributes, and the request itself.

```json
{
  "role": "roles/storage.objectViewer",
  "members": ["group:data-analysts@example.com"],
  "condition": {
    "title": "only_analytics_bucket",
    "expression": "resource.name.startsWith('projects/_/buckets/analytics')",
    "description": "Access limited to the analytics bucket"
  }
}
```

Two properties that matter more than the syntax:

**Conditions fail closed.** If the attribute is missing, the condition does not match, and the binding does not apply. A condition that depends on a resource label therefore grants *nothing* to resources that lack the label — including resources created before you added the label. This is a feature: it is safe by default. It is also a common cause of "my access disappeared and I don't know why" — the label was not applied to the new bucket.

**Conditions are attached to the binding, not the role.** The same role can be granted with a condition at one scope and without at another.

In the course's simulator, a conditional binding whose condition does not match is simply skipped, and if nothing else grants the permission the decision is a denial with the reason `no binding grants <permission> on this resource`.

Conditions on data resources are typically driven by **resource labels**. The pattern: tag a bucket `env=prod`, tag the staging bucket `env=dev`, then grant `roles/storage.objectViewer` to the analysts group with condition `resource.labels.env == 'prod'`. The analysts see production data and not staging — unless a resource is untagged, in which case they see nothing. Pair this with an organization policy that *requires* the `env` label, so untagged resources cannot be created.

### Where to attach a grant, and how to make it

**The scope of the binding determines the blast radius.** Same role, different attachment:

| Attachment | Blast radius |
|---|---|
| Organization | Every resource in every project |
| Folder | Every resource in every project under the folder |
| Project | Every resource in the project |
| Dataset / bucket / topic | That resource and its children |
| Individual object | That object |

The rule I teach: **attach at the narrowest scope that is operationally workable.** It is completely fine for a role to be granted at project level when the project *is* the boundary — for example, a data science sandbox project where one project holds one dataset.

The mechanics, which differ enough to trip people up:

```bash
# Organization level
gcloud organizations add-iam-policy-binding ORGANIZATION_ID \
  --member="group:data-eng@example.com" --role="roles/viewer"

# Folder level
gcloud resource-manager folders add-iam-policy-binding FOLDER_ID \
  --member="group:data-eng@example.com" --role="roles/bigquery.jobUser"

# Project level
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:pipeline@p.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Resource level — a dataset
gcloud bigquery datasets add-iam-policy-binding PROJECT_ID:DATASET_ID \
  --member="serviceAccount:pipeline@p.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Resource level — a bucket
gcloud storage buckets add-iam-policy-binding gs://BUCKET \
  --member="serviceAccount:pipeline@p.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"
```

Note that `gcloud` has per-resource verbs (`gcloud bigquery datasets add-iam-policy-binding`, `gcloud storage buckets add-iam-policy-binding`) and a generic one (`gcloud projects add-iam-policy-binding`). The generic form cannot target a bucket or a dataset. Use the specific verbs.

**Always use `add-iam-policy-binding`, never `set-iam-policy`.** The `set` variants replace the whole policy and will silently delete every other binding. This is the single most destructive command in the GCP CLI, and it has destroyed access in production systems many times. The `add` variants are read-modify-write and preserve existing bindings.

### Groups and service accounts in practice

Two operational patterns worth knowing:

**Domain-wide groups for humans, per-service accounts for workloads.** `group:data-eng@example.com` gets `roles/viewer` on the engineering folder. Each workload gets its own service account with narrow, resource-scoped roles.

**Service account impersonation** for human access to production data. Instead of granting a human `roles/bigquery.dataEditor` on a production dataset, grant a human `roles/iam.serviceAccountViewer` on a service account that *has* `roles/bigquery.dataEditor`, then let the human impersonate it for a limited session:

```bash
gcloud auth print-access-token --impersonate-service-account=analyst-prod@p.iam.gserviceaccount.com
```

Every such call is recorded in Cloud Audit Logs as an impersonation event. This is a genuinely good pattern for regulated environments: access is time-boxed, attributable and revocable by deleting the service account.

---

## 🛠️ Hands-On

### Exercise A — Read the demo project's IAM policy

```bash
cd path/to/gcp-de   # the course root
python project/local_runner.py --iam
```

The output has two halves: the raw policy (bindings by resource) and the *effective access* table with ✓ and ✗ marks. The second half is the one that matters, because it evaluates real permission requests against the policy using the real precedence rules.

### Exercise B — Build an access matrix with the IAM engine

```python
"""Build an effective-access matrix for the demo identities."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from iam_policy import ROLES, ROLE_SUMMARY, evaluate
from platform_sim import build_demo_project

PERMISSIONS = [
    "storage.objects.get",
    "storage.objects.create",
    "storage.objects.delete",
    "bigquery.tables.getData",
    "bigquery.tables.create",
    "pubsub.topics.publish",
    "pubsub.subscriptions.consume",
]

RESOURCES = [
    "projects/gcp-de-course",
    "projects/gcp-de-course/buckets/raw-events-us-central1",
    "projects/gcp-de-course/datasets/curated_us-central1",
    "projects/gcp-de-course/topics/events-us-central1",
]


def main() -> None:
    project = build_demo_project()
    identities = [
        "analytics@example.com",
        "pipeline-sa@gcp-de-course.iam.gserviceaccount.com",
        "stranger@example.com",
    ]

    for resource in RESOURCES:
        print(f"\n=== {resource} ===")
        header = "identity".ljust(52) + "".join(
            p.split(".")[-1][:11].rjust(13) for p in PERMISSIONS
        )
        print(header)
        for identity in identities:
            row = identity.ljust(52)
            for permission in PERMISSIONS:
                decision = evaluate(
                    project.policy, identity, permission, resource=resource
                )
                mark = "yes" if decision.allowed else "-"
                row += mark.rjust(13)
            print(row)


if __name__ == "__main__":
    main()
```

Read the output as a matrix and you can see the design directly: the analyst reads storage and writes BigQuery; the pipeline writes storage and reads/writes BigQuery and Pub/Sub; the stranger gets nothing.

### Exercise C — Test the role semantics that surprise people

```python
"""Verify the counter-intuitive role semantics."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from iam_policy import Binding, Policy, Principal, evaluate


def check(role: str, permission: str, resource: str = "projects/p") -> bool:
    policy = Policy()
    policy.add(Principal("user", "u@example.com"), Binding(role), resource="projects/p")
    return evaluate(policy, "u@example.com", permission, resource=resource).allowed


def main() -> None:
    cases = [
        ("roles/storage.objectViewer", "storage.objects.get", True),
        ("roles/storage.objectViewer", "storage.objects.create", False),
        ("roles/storage.objectCreator", "storage.objects.create", True),
        ("roles/storage.objectCreator", "storage.objects.get", False),
        ("roles/bigquery.dataViewer", "bigquery.tables.getData", True),
        ("roles/bigquery.dataViewer", "bigquery.tables.create", False),
        ("roles/bigquery.jobUser", "bigquery.jobs.createQuery", True),
        ("roles/bigquery.jobUser", "bigquery.tables.getData", False),
        ("roles/viewer", "storage.objects.get", True),
        ("roles/viewer", "storage.objects.create", False),
        ("roles/editor", "storage.objects.create", True),
        ("roles/editor", "resourcemanager.projects.setIamPolicy", False),
        ("roles/owner", "resourcemanager.projects.setIamPolicy", True),
        ("roles/owner", "storage.objects.get", True),
    ]

    failures = 0
    for role, permission, expected in cases:
        actual = check(role, permission)
        status = "ok " if actual == expected else "FAIL"
        if actual != expected:
            failures += 1
        print(f"{status} {role:<34} {permission:<42} expected={expected!s:<6} actual={actual}")

    print(f"\n{len(cases) - failures}/{len(cases)} expectations met")


if __name__ == "__main__":
    main()
```

Every one of these expectations holds in the real platform, and each one is a support ticket somewhere.

### Exercise D — Measure blast radius with `blast_radius`

```python
"""What can each identity reach?"""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from iam_policy import blast_radius, explain_principal
from platform_sim import build_demo_project

RESOURCES = [
    "projects/gcp-de-course/buckets/raw-events-us-central1",
    "projects/gcp-de-course/datasets/curated_us-central1",
    "projects/gcp-de-course/topics/events-us-central1",
]


def main() -> None:
    project = build_demo_project()

    for identity in ("analytics@example.com",
                     "pipeline-sa@gcp-de-course.iam.gserviceaccount.com"):
        print("=" * 72)
        print(identity)
        print("=" * 72)
        for line in explain_principal(
            project.policy, identity, resource=RESOURCES[0]
        ):
            print(f"  {line}")

        reachable = blast_radius(project.policy, identity, RESOURCES)
        print("\nresources reachable:")
        for resource, ok in sorted(reachable.items()):
            mark = "yes" if ok else "no "
            print(f"  {mark} {resource}")


if __name__ == "__main__":
    main()
```

The output for the analyst shows two project-level ALLOW bindings — one `roles/bigquery.dataEditor`, one `roles/storage.objectViewer` — inherited by every resource in the project. Ask yourself: if this person's laptop were stolen tomorrow, what would the attacker reach, and in how many projects?

### Exercise E — Grant and revoke on the live platform

```bash
# Inspect before changing
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.members)" \
  --limit=100

# Grant at the narrowest sensible scope
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="group:data-eng@example.com" \
  --role="roles/bigquery.jobUser"

# Grant on a single dataset
gcloud bigquery datasets add-iam-policy-binding PROJECT_ID:curated_us-central1 \
  --member="group:analytics@example.com" \
  --role="roles/bigquery.dataViewer"

# Verify
gcloud bigquery datasets get-iam-policy PROJECT_ID:curated_us-central1 \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.members)"

# NEVER use set-iam-policy — it replaces the entire policy.
# gcloud projects set-iam-policy PROJECT_ID policy.json   # destructive
```

### Exercise F — Create a service account with a scoped role

```bash
# Create
gcloud iam service-accounts create dp-landing-writer \
  --display-name="Data Platform Landing Writer" \
  --description="Writes raw events to the landing bucket. No read access."

# Grant it only what it needs, on one bucket
gcloud storage buckets add-iam-policy-binding gs://PROJECT_ID-raw-us-central1 \
  --member="serviceAccount:dp-landing-writer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"

# Who can act as it? (should be an empty or tightly-controlled list)
gcloud iam service-accounts get-iam-policy \
  dp-landing-writer@PROJECT_ID.iam.gserviceaccount.com \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.members)"

# List every service account and the roles it holds
gcloud iam service-accounts list --project PROJECT_ID --format="table(email, displayName)"
for sa in $(gcloud iam service-accounts list --project PROJECT_ID --format="value(email)"); do
  echo "--- $sa"
  gcloud iam service-accounts get-iam-policy "$sa" \
    --flatten="bindings[].members" --format="value(bindings.role)"
done
```

That last loop is the quarterly review ritual, and it finds things. Usually it finds a service account with `roles/owner` that somebody granted "temporarily" in 2023.

---

## 🛠️ Common Errors and Fixes

### Error 1 — `ERROR: (gcloud.projects.add-iam-policy-binding) The principal (user or service account) does not exist.`

**When:** You grant a role to a service account that does not exist yet, or to a user address that has no Google account.

**Why:** IAM will not create identities implicitly. A service account must exist before it can be a member of a binding, and a user principal must correspond to a real account in your Cloud Identity domain.

**Fix:** Create the service account first, then bind. For a user, confirm the address is a real account.

```bash
gcloud iam service-accounts create dp-landing-writer --display-name="Landing Writer"
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:dp-landing-writer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### Error 2 — `ERROR: (gcloud.iam.service-accounts.add-iam-policy-binding) The service account does not exist.`

**When:** You used the wrong domain in the member string.

**Why:** The member string must be `serviceAccount:EMAIL@PROJECT_ID.iam.gserviceaccount.com` — the *project ID*, not the display name, and the fully-qualified service account domain, not `example.com`.

**Fix:** Derive the exact address from the API, never type it.

```bash
SA=$(gcloud iam service-accounts list --project PROJECT_ID --filter="displayName:Landing" --format="value(email)")
echo "$SA"
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --member="user:you@example.com" --role="roles/iam.serviceAccountUser"
```

### Error 3 — `PERMISSION_DENIED: Permission 'storage.objects.get' denied on resource 'projects/PROJECT_ID/buckets/BUCKET'.`

**When:** A service account or user that "has access" tries to read an object.

**Why:** Almost always one of four things: (a) the role is `roles/storage.objectCreator`, which creates but cannot read; (b) the grant was made at the project but the *resource* is in a different project; (c) uniform bucket-level access is on and the object has a per-object ACL that confuses a human; (d) an explicit DENY policy is overriding the ALLOW.

**Fix:** Diagnose in this order — read the effective policy, check the role's permission set, then look for a DENY.

```bash
gcloud storage buckets get-iam-policy gs://BUCKET \
  --flatten="bindings[].members" --format="table(bindings.role, bindings.members)"
gcloud storage buckets get-iam-policy gs://BUCKET --flatten="bindings[].members" \
  --format="value(bindings.condition.expression)" | grep -i deny
```

In the course's model, `roles/storage.objectCreator` grants `storage.objects.create` and `storage.buckets.get` — but **not** `storage.objects.get`. That asymmetry is intentional and is the mechanism behind this error.

### Error 4 — `ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'iam.serviceaccounts.actAs' denied on service account 'projects/PROJECT_ID/serviceAccounts/NAME@PROJECT_ID.iam.gserviceaccount.com'`

**When:** You deploy to Cloud Run, GKE or Cloud Functions and specify a runtime service account you do not have permission to act as.

**Why:** Deploying as a service account requires `iam.serviceAccounts.actAs`. Deploying *with* the default compute service account requires no special grant — which is why the error only appears when you choose a specific account.

**Fix:** Grant `roles/iam.serviceAccountUser` on that one service account.

```bash
gcloud iam service-accounts add-iam-policy-binding \
  NAME@PROJECT_ID.iam.gserviceaccount.com \
  --member="user:you@example.com" \
  --role="roles/iam.serviceAccountUser"
```

### Error 5 — `ERROR: (gcloud.projects.set-iam-policy) INVALID_ARGUMENT: Policy is invalid: ... : Invalid principal`

**When:** A `set-iam-policy` with a hand-written JSON file is rejected.

**Why:** Two common causes: the JSON is malformed (the `bindings` key is wrong), or the principal string uses an invalid prefix. Valid prefixes are `user:`, `group:`, `domain:`, `serviceAccount:`, `principal:`, `principalSet:`, `deleted:`, `projectOwner:`, `projectEditor:`, `projectViewer:`.

**Fix:** Prefer `add-iam-policy-binding`, which validates members for you. If you must set a policy, generate it with `--format=json` from the current policy, edit it, and re-apply — never write it from scratch.

```bash
gcloud projects get-iam-policy PROJECT_ID --format=json > policy.json
# edit policy.json carefully, then:
gcloud projects set-iam-policy PROJECT_ID policy.json
```

### Error 6 — Access worked yesterday and silently stopped today

**When:** A binding with a condition stops applying.

**Why:** The condition depends on a resource attribute — most often a **label**. The resource was recreated, or a new version was deployed without the label, and the condition no longer matches. Conditions fail closed, so the grant disappears without an error message.

**Fix:** Inspect the condition and the resource's current labels.

```bash
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role, bindings.condition.expression, bindings.members)"
gcloud storage buckets describe gs://BUCKET --format="value(labels)"
```

A closely related surprise is `PERMISSION_DENIED: Permission 'resourcemanager.projects.setIamPolicy' denied on resource 'projects/PROJECT_ID'` when you try to change IAM on a project while holding `roles/editor`. `roles/editor` deliberately excludes that permission, as does `roles/viewer`; only `roles/owner` and `roles/resourcemanager.projectIamAdmin` can change IAM. This error is a feature — it is the mechanism that stops an editor from escalating to owner. Ask an owner for `roles/resourcemanager.projectIamAdmin` on that project only, or have them run the grant.

---

## 💡 Production Notes

- **Never use `set-iam-policy` in production.** It replaces the entire policy. Use `add-iam-policy-binding` / `remove-iam-policy-binding` / `set-iam-policy-binding` (which only replaces bindings for *one* role and one member set).
- **Grant `roles/iam.serviceAccountUser` on individual service accounts, never `roles/iam.serviceAccountAdmin` at project scope.** The latter grants `actAs` on every service account in the project, which is project-wide impersonation of every workload.
- **Give every service account a purpose-built name.** `dp-landing-writer` is searchable in Cloud Audit Logs and self-documenting in an incident. `sa-1` is neither.
- **Enable Cloud Audit Logs and read them.** `gcloud projects get-iam-policy` shows the current state; Audit Logs show who changed it. The `protoPayload.authenticationInfo.principalEmail` and `serviceAccount` fields answer "who was this, really" for every API call.
- **Review service account inventory quarterly.** Delete unused accounts. A service account that holds `roles/owner` and runs nothing is a live key waiting to be used by someone.
- **Rotate keys deliberately, or better, delete them.** Workloads on GKE, Cloud Run, Dataflow and Composer obtain credentials automatically from the metadata server — they need **no keys at all**. Keys exist for external systems, and every key you create is a credential you must rotate.
- **Use groups for humans, and bind groups at the folder level** where possible. Group membership changes then need no IAM operation at all, which removes the most common source of stale access.
- **Apply conditional bindings for time-boxed access, not permanent roles.** For example, grant a release role with condition `request.time < timestamp("2026-12-31T00:00:00Z")`. The access expires without anybody having to remember to revoke it.

---

## 🔑 Key Takeaways

- IAM evaluates in a fixed order: **DENY wins, then ALLOW, then deny by default**. There is no implicit allow.
- Four identity types — **user, group, service account, domain** — and groups are the right unit for human access.
- **Primitive roles are broad and dangerous**; predefined roles are the default; custom roles fill genuine gaps.
- The counter-intuitive semantics that cause real tickets: `roles/storage.objectCreator` **cannot read**; `roles/bigquery.dataViewer` **cannot create tables** but can run queries; `roles/bigquery.jobUser` can run queries but **cannot read results**; `roles/editor` **cannot** change IAM; `roles/owner` can.
- The **three service-account questions** — who is it, who can impersonate it, what is the blast radius — must all be answered before attaching it.
- **Least privilege is a workflow**: read the code, grant at the resource, pick the narrowest role, split by phase, re-review quarterly.
- **Conditional bindings fail closed**, which is safe by default and surprising when a label goes missing.
- **Binding scope is the blast radius.** A project-level `roles/bigquery.dataEditor` reaches every table in the project; a dataset-level one reaches one dataset.

---

## 📚 Practice Exercises

1. Run `python project/local_runner.py --iam` and write down, for each of the seven checks, the exact reason the decision came out that way. Then change one binding in `platform_sim.build_demo_project()` and show which checks flip.
2. Using `iam_policy.ROLES`, print a table of the 23 roles with the number of permissions each grants, sorted descending. Which three roles would you never grant to anyone, and why?
3. Write a script that proves the precedence rule in all three cases: (a) ALLOW alone → allowed; (b) ALLOW plus explicit DENY → denied; (c) DENY at a child resource overriding an ALLOW inherited from the project. Print the `reason` string for each.
4. Take the demo project and write a variant where `analytics@example.com` gets `roles/storage.objectCreator` instead of `roles/storage.objectViewer`. Run the effective-access table and explain precisely why the analyst can now write a file to the landing bucket but still cannot read one — including which permission is present and which is missing.
5. Design the IAM model for a three-tier pipeline: a landing service (writes only), a transformation service (reads raw, writes curated), and an analyst group (reads curated only). State the exact role for each principal, the exact scope it is attached to, and the blast radius of each in one sentence. Verify your design by constructing the `Policy` in Python and printing the effective-access matrix.
6. Use `blast_radius` on the demo project. Compare the reach of `analytics@example.com` with what a hypothetical `user:admin@example.com` holding `roles/owner` would reach. Then write down what an attacker would do with each credential if it leaked.
7. On a real project, list every service account, every role it holds, and every human who holds `iam.serviceAccounts.actAs` on it. Produce a table. Identify any account that holds a role it does not need, and write the exact `gcloud` command to remove it.
8. Write a conditional binding in JSON that grants `roles/storage.objectViewer` to `group:analysts@example.com` only on buckets labelled `env=prod`. Then explain what happens to a bucket with **no** `env` label, and to a bucket with `env=staging`.

---

## 📖 Further Reading
- [Identity and Access Management Overview](https://cloud.google.com/iam/docs/overview)
- [Understanding Roles](https://cloud.google.com/iam/docs/understanding-roles)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Service Account Impersonation](https://cloud.google.com/iam/docs/service-account-impersonation)
- [Conditions Overview](https://cloud.google.com/iam/docs/conditions-overview)
- [Denies Overview](https://cloud.google.com/iam/docs/deny-overview)
- [Least Privilege](https://cloud.google.com/iam/docs/least-privilege)
