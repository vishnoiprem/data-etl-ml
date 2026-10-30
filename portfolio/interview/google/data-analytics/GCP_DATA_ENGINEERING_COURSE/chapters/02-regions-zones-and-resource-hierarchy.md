# 1.2 — Regions, Zones & the Resource Hierarchy

> **Section 1 · GCP Fundamentals · Lecture 1.2 · 8:00**

## 🎯 What you will learn
- What a region, a zone and a multi-region actually are, mechanically
- Why zones exist and what a zonal outage means for your data
- The resource hierarchy: organization → folder → project → resource, and how inheritance flows downward
- Project ID versus project name — and why getting this wrong breaks automation
- Where to place a resource, using three axes: latency, data residency and cost
- How Cloud Shell and Cloud Editor work, and when each is the right tool
- How to design a project layout that survives a team of twenty

---

## 🧠 Concept

### Regions and zones: the physical substrate

Google Cloud's geography is built from three concepts, each corresponding to a level of physical abstraction.

A **zone** is a deployment location within a region. It is a physically separate data centre with independent power, cooling and networking. A region always has at least three zones — this course models exactly three per region, with the suffixes `-a`, `-b` and `-c`. Zones within a region are connected by low-latency fibre (typically sub-millisecond within a region), but they are still independently failure domains.

A **region** is a geographic location containing at least three zones. The regions in this course are:

| Region | Display name | Region | Display name |
|---|---|---|---|
| `us-central1` | Iowa | `asia-south1` | Mumbai |
| `us-east1` | South Carolina | `asia-southeast1` | Singapore |
| `us-east4` | Northern Virginia | `asia-northeast1` | Tokyo |
| `us-west1` | Oregon | `australia-southeast1` | Sydney |
| `europe-west1` | Belgium | `southamerica-east1` | São Paulo |
| `europe-west2` | London | | |
| `europe-west4` | Netherlands | | |

A **multi-region** is two or more regions grouped so that a single global namespace serves data replicated across them. Cloud Storage multi-regions are `US`, `EU`, `ASIA` and `AUSTRALIA`. A multi-region is a *data placement* construct: it does not give you compute in both regions, and a multi-region bucket has a higher storage price than a regional bucket (because the data is replicated) but a much better availability story.

The distinction that trips people up: **a regional resource is not available across the region.** A Cloud Storage bucket created in `us-central1` is physically located in `us-central1`; it is not "in the region" in the sense of being served from any of the three zones. Regional buckets replicate across the region's zones automatically for durability, but every read and write is served from that one geography.

### Why zones exist, and what a zonal outage costs you

A zone is a failure domain. Power loss, cooling failure, a fibre cut, or a hypervisor bug can take an entire zone down. Google designs regions so that a zonal outage is a routine, survivable event — which means *your architecture must be able to survive one*, because Google cannot save you from one.

Mechanically, what survives a zonal outage depends on the resource:

- **A Compute Engine instance** with a zonal persistent disk dies with the zone. You need a second instance in another zone, and you need the disk contents replicated.
- **A regional persistent disk** replicates across the zones of one region and can be attached to an instance in any of them. It survives a zonal failure but not a regional one.
- **A Cloud Storage bucket** is inherently highly available: objects are stored redundantly across multiple locations within the region (or across regions for a multi-region). You do not need to do anything.
- **BigQuery** is a multi-region service internally. A dataset location determines where your *data* is stored, but the compute serving your query can run anywhere Google has capacity. Data residency still matters legally and for cross-region data movement cost.
- **A GKE cluster** is regional by default and spreads its nodes across zones in that region. If you create a zonal cluster (a legacy, discouraged choice), a zonal outage takes down the control plane.

The practical takeaway for a data engineer: **cross-zone replication is a design decision for stateful components.** Stateless compute (a Dataflow worker pool, a Cloud Run service) is handled by the platform if you deploy regionally.

### The resource hierarchy

Google Cloud's organisational structure is a strict tree. Four levels, each nesting inside the one above:

```text
organization
└── folder
    └── folder
        └── project
            └── resource  (bucket, dataset, topic, instance, cluster, ...)
```

**The organization** is the top-level container for your entire Google Cloud estate. Only one organization per Cloud Identity (or Workspace) domain, and only a handful of Google accounts ever become organization admins. You do not create one; your enterprise IT team does. But as a data engineer you will meet it constantly, because it is where organization policies and central IAM live.

**Folders** are intermediate containers. They exist for three reasons: grouping projects by team, by environment, or by data domain; attaching IAM bindings that should apply to many projects at once; and attaching organization policies that should apply to many projects at once. Folders nest arbitrarily deep, but in practice three levels is enough; deeper nesting usually means you are using folders to encode an org chart rather than an access boundary.

**Projects** are the central unit of billing, IAM, quotas and API enablement. Every API call names a project. Every bill line item attributes to a project. Almost every bug in a GCP setup is a project boundary in the wrong place.

**Resources** are the things that do work: Cloud Storage buckets, BigQuery datasets, Pub/Sub topics, Compute Engine instances, GKE clusters, Cloud Run services.

### Inheritance: the rule that decides every access question

IAM bindings and organization policies flow **downward only**. A binding on the organization applies to every folder, project and resource beneath it. A binding on a folder applies to its projects and their resources. A binding on a project applies to that project's resources.

Two consequences follow, and they are the source of most security incidents:

1. **A grant on a parent is always inherited by the child.** You cannot "opt out" of a parent binding by adding a narrower one — you can only add a narrower binding (which adds permissions), or use an explicit DENY.
2. **An explicit DENY beats any ALLOW, at any level.** This is the escape hatch, and it is why deny policies exist: to carve a narrow exception out of a broad inherited grant.

The course project models exactly this. A role granted at `projects/p` applies to `projects/p/buckets/b`; the simulator's `ancestor_paths()` function walks the resource path in *type/name pairs*, because a GCP resource path is not a flat list of segments:

```text
projects/p/buckets/b/objects/o
projects/p/buckets/b
projects/p
```

Note what is **not** in that ancestry: `projects/p/buckets/b/objects` and `projects/p/buckets`. Those are not real IAM scopes. A binding on a non-existent scope does nothing, which is a surprisingly common misconfiguration.

### Project ID versus project name

This distinction causes more automation failures than any other conceptual gap in GCP.

| | Project ID | Project name |
|---|---|---|
| Format | Globally unique, 6–30 chars, lowercase letters, digits, hyphens | Free-form, 4–30 chars, spaces allowed |
| Mutable | **No** — it cannot be changed after creation | Yes |
| Global | Yes — unique across all of Google Cloud | No — two projects can share a name |
| Used by | APIs, `gcloud` commands, service account emails | Console display only |

Consequences worth internalising:

- **A service account email embeds the project ID**: `pipeline-sa@gcp-de-course.iam.gserviceaccount.com`. Change the display name and the email does not change — good. Change the ID and you have orphaned every IAM binding, every key file, every scheduler target, and every log sink that referenced it — and you cannot change it back.
- **Project IDs are not recycled.** Once `demo-project` has existed, nobody else can ever use it. This is why `gcloud projects create` fails with "Requested entity already exists" for names that look obviously available.
- **Never parse a project name.** If your code does `PROJECT.split("-")[0]` on a display name to get the ID, it will break the first time someone renames the project in the console.

In automation, always treat the project ID as a configuration value with an environment-specific value per environment, and never derive it from a display name.

### Where to put resources: three axes

"Which region?" is never a single-dimensional question. It is three questions, and they can conflict.

**Axis 1 — Latency.** Place compute near the data it reads and near the users it serves. A BigQuery dataset in `europe-west4` queried by a GKE cluster in `europe-west1` pays cross-region network latency on every query and, for BigQuery specifically, the bytes are processed in the dataset's location — you cannot move that. The specific trap: a Cloud Storage bucket in `europe-west1` and a Dataflow job in `us-central1` will read the data across the Atlantic. Dataflow bills inter-region egress at a reduced rate versus internet egress, but it is still charged and it is still milliseconds.

**Axis 2 — Data residency and regulation.** Certain jurisdictions have data-locality laws. If the client operates in the EU, the German Energiewende data is German, or the data must stay in-country, then residency is a legal constraint, not a preference. The mechanics on GCP: Cloud Storage buckets are pinned to a region or multi-region; BigQuery datasets are pinned to a location; Cloud SQL instances are regional; Spanner instances span a set of regions. Regional products cannot be moved — you must copy the data to a new location.

**Axis 3 — Cost.** Prices differ by region. `us-central1` is typically the cheapest US region; `us-east1` and `us-west1` are close. European and Asia-Pacific regions are usually more expensive. Two concrete examples from the platform:

- **The free tier is region-scoped.** The always-free Compute Engine `e2-micro` allowance applies only in `us-central1`, `us-east1` and `us-west1`. The always-free Cloud Storage allowance applies only in `us-central1`, `us-east1` and `us-west1`. The same workload in `europe-west4` is billed in full.
- **Egress pricing varies by source and destination.** Moving data from `us-central1` to the internet is $0.12/GB in this course's model. Moving data between GCP regions is cheaper; moving data *into* GCP is free.

When the three axes conflict, here is the decision order I use:

1. **Legal constraints are non-negotiable.** Residency wins over latency and cost.
2. **Data gravity beats user proximity for data processing.** A global pipeline that reads a 40 TB dataset should process in the same region as the data. Moving compute to be near the user is a mistake when the compute touches all the data.
3. **Then cost, then latency.** Pick the cheapest region that satisfies the first two, and add a second region only when the workload genuinely needs it.

A fourth consideration that is often decisive in practice: **service availability.** The course's region matrix shows exactly this. `BigLake` is in preview in `southamerica-east1`; `Datastore` is restricted there; `Memorystore` is restricted; `Data Fusion` is in preview in `southamerica-east1` and restricted in `australia-southeast1`; `BigQuery ML` has no availability marker in `southamerica-east1` at all. If you place a BigLake-backed lakehouse in São Paulo, you are running on a preview service with no SLA and a contract that can change.

### Designing the layout

The layout decision cascades. Once you place projects, you have decided who can see what, how billing is segmented, and how painful a resource deletion is.

My default layout for a data platform in an organisation:

```text
organization: acme.example.com
├── folder: data-platform
│   ├── folder: production
│   │   ├── project: acme-dp-prod-landing
│   │   ├── project: acme-dp-prod-curated
│   │   └── project: acme-dp-prod-analytics
│   ├── folder: non-production
│   │   ├── project: acme-dp-dev-landing
│   │   └── project: acme-dp-dev-analytics
├── folder: data-science
│   ├── project: acme-ds-sandbox
│   └── project: acme-ds-experiments
└── folder: shared-services
    └── project: acme-shared-data-governance
```

Principles behind it:

- **Landing, curated and analytics are separate projects** because they have different access models. A landing zone is write-once from producers and read-only for most consumers; curated is written by transformation jobs; analytics is read-only for the business. Splitting them lets you grant `roles/storage.objectViewer` on raw data to analysts without letting them delete it.
- **Environment is a folder, not a project suffix convention.** A folder lets you attach a single restrictive organization policy to all non-production projects — a powerful guardrail that is impossible to apply consistently by convention alone.
- **Shared governance lives in its own project.** Data Catalog tag templates, DLP templates and Dataplex lakes span projects; putting them in one project keeps the taxonomy coherent and separately budgetable.
- **Sandbox is isolated.** `acme-ds-sandbox` is where people experiment, and it is the project most likely to burn budget. It should have its own budget alert and its own quotas.

### Cloud Shell

Cloud Shell is a managed Debian environment with `gcloud`, `kubectl`, `docker`, `git`, `curl` and an editor preinstalled. It authenticates through your browser session, so there is no key file to leak, and it persists a home directory between sessions (5 GB, in the home region of your Cloud Shell configuration).

Use Cloud Shell when:

- You need the `gcloud` CLI but do not want to install it locally (macOS Homebrew, Windows via the MSI installer, Linux via apt).
- You are demonstrating a walkthrough to a team and want everyone on identical tooling versions.
- You need a quick place to run `gcloud` commands without managing credentials on a shared machine.

Do **not** use Cloud Shell as your production deployment workstation for anything long-lived. The instance is ephemeral (5 hours idle by default), it is a single point of failure for interactive work, and long-running commands can be killed. For repeatable infrastructure, commit the commands to a script or a Terraform module and run them from CI.

The authentication model deserves one warning: Cloud Shell uses the credentials of the **account you are signed into in the browser**, not of the `gcloud` configuration you think you set. If you run `gcloud auth list` in Cloud Shell and see a different account than expected, sign out of the wrong Google account in the browser, not with `gcloud auth revoke`.

### Cloud Editor

Cloud Editor is the browser-based IDE built into Google Cloud, based on Code OSS (the open-source VS Code). It provides:

- A code workspace, optionally on a Compute Engine VM (with a persistent disk) or in an ephemeral in-browser container.
- A preconfigured terminal with `gcloud` and the language toolchains already installed.
- Git integration backed by Secret Manager for credentials.
- A built-in notebook (Jupyter) for exploratory data work.
- The ability to open the console, shell, and editor in a single pane layout, which is genuinely useful for tutorials.

Choose between them:

| Need | Use |
|---|---|
| One-off CLI commands, quick bucket inspection | Cloud Shell |
| Editing a multi-file project, writing Terraform or a Dataflow job | Cloud Editor |
| Interactive SQL analysis with a visual result grid | BigQuery console |
| A repeatable pipeline, committed and scheduled | Dataform / Composer / Dataflow templates |

The engineering answer that matters: **Cloud Editor is a convenience for authoring; a repository is the source of truth.** Whatever you write in Cloud Editor must end up in Git, because the thing you schedule, review and roll back is the committed version, not the browser tab.

---

## 🛠️ Hands-On

### Exercise A — Explore regions and zones locally

The course's service catalogue contains all 12 regions and models zones within them.

```python
"""Map services to regions using the course's service catalogue."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from service_catalog import REGIONS, zones_in, services_available_in


def main() -> None:
    coverage = []
    for region in REGIONS:
        zones = zones_in(region)
        available = services_available_in(region)
        coverage.append((len(available), region))
        print(f"{region:<22} {REGIONS[region]:<20} zones={len(zones)} services={len(available)}")

    best = max(count for count, _ in coverage)
    winners = sorted(region for count, region in coverage if count == best)
    print(f"\nwidest coverage: {best} services in {', '.join(winners)}")

    narrowest = min(count for count, _ in coverage)
    losers = sorted(region for count, region in coverage if count == narrowest)
    print(f"narrowest coverage: {narrowest} services in {', '.join(losers)}")


if __name__ == "__main__":
    main()
```

Expected output (abridged):

```text
us-central1            Iowa                 zones=3 services=34
us-east1               South Carolina       zones=3 services=34
...
australia-southeast1   Sydney               zones=3 services=30
southamerica-east1     São Paulo            zones=3 services=23

widest coverage: 34 services in asia-northeast1, asia-south1, asia-southeast1, europe-west1, europe-west2, europe-west4, us-central1, us-east1, us-east4, us-west1
narrowest coverage: 23 services in southamerica-east1
```

Ten regions have identical service coverage; the two that do not are the two with preview or restricted services. This is the availability problem in one number — **southamerica-east1 gives you 23 of the 34 generally-available services.**

### Exercise B — Read the resource tree

```bash
cd path/to/gcp-de   # the course root
python project/local_runner.py --run
```

Expected output begins:

```text
organization: acme.example.com
└── folder: engineering
    └── project: GCP Data Engineering Course (gcp-de-course)
        ├── dataset: curated_us-central1  [BigQuery]
        ├── topic: events-us-central1  [Pub/Sub]
        ├── bucket: raw-events-us-central1  [Cloud Storage]
        └── serviceAccount: pipeline-sa@gcp-de-course.iam.gserviceaccount.com
```

Note the resource *names* encode their location: `raw-events-us-central1`, `curated_us-central1`, `events-us-central1`. That is a deliberate convention — the location suffix in the name makes an accidental cross-region move visible in code review.

### Exercise C — Inspect the live hierarchy with gcloud

```bash
# Which project am I actually in?
gcloud config get-value project
gcloud projects describe $(gcloud config get-value project) --format="table(projectId, name, parent)"

# What are the organizations and folders I can see?
gcloud resource-manager folders list --project=$(gcloud config get-value project)

# Which resources does this project contain, and where are they?
gcloud storage buckets list --project YOUR_PROJECT_ID --format="table(name, location, storageClass)"
gcloud bigquery datasets list --project YOUR_PROJECT_ID --format="table(datasetId, location, labels)"

# Every enabled API and its quota
gcloud services list --enabled --project YOUR_PROJECT_ID --format="table(config.name, config.title)"
```

### Exercise D — Demonstrate that inheritance is downward

This is the single most important property of the hierarchy. Prove it with the course's IAM engine.

```python
"""Show that a project-level grant is inherited by a bucket."""
import sys
from pathlib import Path

sys.path.insert(0, "project/core")

from iam_policy import Binding, Policy, Principal, evaluate


def main() -> None:
    policy = Policy()
    analyst = Principal("user", "ana@example.com")

    # One grant, at the project level only.
    policy.add(analyst, Binding("roles/storage.objectViewer"), resource="projects/p")

    resource = "projects/p/buckets/raw"
    decision = evaluate(policy, "ana@example.com", "storage.objects.get", resource=resource)
    print(f"allowed: {decision.allowed}")
    print(f"reason:  {decision.reason}")
    print(f"inherited: {decision.inherited}")

    # Now prove an explicit DENY beats the inherited ALLOW.
    policy.deny(analyst, "roles/storage.objectViewer", resource="projects/p/buckets/raw")
    decision = evaluate(policy, "ana@example.com", "storage.objects.get", resource=resource)
    print(f"\nafter DENY on the bucket:")
    print(f"allowed: {decision.allowed}")
    print(f"reason:  {decision.reason}")


if __name__ == "__main__":
    main()
```

Expected output:

```text
allowed: True
reason:  storage.objects.get is inherited from an ancestor of the resource via roles/storage.objectViewer
inherited: True

after DENY on the bucket:
allowed: False
reason:  explicit DENY on roles/storage.objectViewer overrides the ALLOW on roles/storage.objectViewer
```

### Exercise E — Create a project and a correctly-named bucket

```bash
# Create with a globally unique id
gcloud projects create gcp-de-$USER-$(date +%s | tail -c 5) --name="GCP DE Lab"

# Record the id, not the name
export PROJECT_ID=$(gcloud projects list --filter="name='GCP DE Lab'" --format="value(projectId)")
echo "project id: $PROJECT_ID"

# Create a bucket whose name encodes its location
gcloud storage buckets create gs://gcp-de-$USER-$PROJECT_ID-us-central1 \
  --location=us-central1 \
  --uniform-bucket-level-access

# Confirm the location was applied
gcloud storage buckets describe gs://gcp-de-$USER-$PROJECT_ID-us-central1 \
  --format="table(name, location, storageClass, iamConfiguration.bucketPolicyOnly.enabled)"

# Upload and read back
echo "hello" | gcloud storage cp - gs://gcp-de-$USER-$PROJECT_ID-us-central1/hello.txt
gcloud storage cat gs://gcp-de-$USER-$PROJECT_ID-us-central1/hello.txt
```

### Exercise F — Compare regions for the same service

```bash
# Which locations offer BigQuery in your project?
gcloud bigquery locations list --project YOUR_PROJECT_ID --filter="type=analytics" --format="table(location, labels)"

# Compare the regions' processing capacity by looking at the locations list
gcloud compute regions list --project YOUR_PROJECT_ID --format="table(name, status, zones[])" | head -20
```

Then cross-check against the course's own matrix:

```bash
python project/local_runner.py --regions
```

You will see the preview and restricted markers (for example `BigLake` is preview in `southamerica-east1`, `Memorystore` is restricted there) — these are exactly the services you should not build a production platform on.

---

## 🛠️ Common Errors and Fixes

### Error 1 — `ERROR: (gcloud.storage.buckets.create) HTTPError 409: Conflict. Could not create bucket. Another bucket with this name already exists.`

**When:** You create a bucket named after your project.

**Why:** Cloud Storage bucket names live in a **single global namespace**, not per project. `gs://my-bucket` is unique across all of Google Cloud forever. This is a deliberate design choice: it makes bucket URLs globally unambiguous and lets IAM and DNS-style references work without a project qualifier.

**Fix:** Include the project ID (or a random suffix) in the bucket name, and prefer making bucket names *region-specific* so the location is visible in the name.

```bash
gcloud storage buckets create gs://$PROJECT_ID-raw-us-central1 --location=us-central1
```

### Error 2 — `ERROR: (gcloud.billing.projects.link) The project ... is not in a valid state, or the account is not in a valid state`

**When:** You link a project to a billing account and immediately try to create billable resources.

**Why:** Newly created projects and billing accounts both need time to propagate through the billing system. The link operation is asynchronous and sometimes appears to succeed before it is committed.

**Fix:** Wait, then re-check the link. Confirm the billing account ID rather than its display name.

```bash
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID
```

### Error 3 — `ERROR: (gcloud.compute.instances.create) The zone 'projects/PROJECT_ID/zones/us-central1-c' does not exist`

**When:** You request a zone that does not exist in the region.

**Why:** Zones are region-specific. `us-central1-c` exists; `europe-west4-c` exists; but `us-east4-c` may not, and `australia-southeast1-b` is not a valid zone at all in some regions. The suffix letters are not uniform across regions.

**Fix:** List the actual zones before requesting one, and prefer the region flag so GCP picks a zone for you.

```bash
gcloud compute zones list --project YOUR_PROJECT_ID --filter="region eq us-central1"
gcloud compute instances create vm1 --zone=us-central1-b
```

### Error 4 — `ERROR: (gcloud.bigquery.datasets.create) Access Denied: BigQuery BigQuery: Permission bigquery.datasets.create denied on resource projects/PROJECT_ID`

**When:** You create a BigQuery dataset with a user who only has read access.

**Why:** `roles/bigquery.dataViewer` grants `bigquery.tables.getData` — reading table data — but **not** `bigquery.datasets.create`. Creating a dataset is a metadata operation on the project, not a data read. This is the single most common BigQuery permission surprise, and it is modelled exactly in the course project: `analytics@example.com` has `roles/bigquery.dataViewer` and `roles/storage.objectViewer`, and the check for `bigquery.tables.create` on `projects/gcp-de-course/datasets/curated` is a ✗.

**Fix:** Grant `roles/bigquery.dataEditor` (data + schema) or `roles/bigquery.dataOwner` (data + schema + ACLs and delete) at the dataset level, and grant `roles/bigquery.jobUser` project-wide so the user can run queries without seeing data they should not.

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:you@example.com" \
  --role="roles/bigquery.jobUser"

gcloud bigquery datasets add-iam-policy-binding your_dataset \
  --member="user:you@example.com" \
  --role="roles/bigquery.dataEditor"
```

### Error 5 — `ERROR: (gcloud.storage.buckets.create) The resource 'projects/_/buckets/your-bucket' already exists`

**When:** You try to recreate a bucket in a different project.

**Why:** Same global-namespace rule as Error 1, but the message names the *global* resource path, which is confusing when you believe you are in a different project.

**Fix:** Use a unique bucket name, or delete the original bucket if you truly own it (bucket names can be recycled after deletion, unlike project IDs).

### Error 6 — `ERROR: (gcloud.resource-manager.folders.create) The caller does not have permission 'resourcemanager.folders.create' on the parent resource`

**When:** You try to create a folder in an organisation you can see in the console but do not administer.

**Why:** Seeing the organisation in a dropdown is not permission to create folders in it. Folder creation requires `resourcemanager.folders.create` on the **parent** — the organisation or the parent folder.

**Fix:** Ask the organisation admin to create the folder and grant you `roles/resourcemanager.folderAdmin` on it. Do not attempt to escalate by asking for `roles/owner` at the organisation level; that role can also change organisation policy and delegate the entire domain.

A related trap sits one level down: **project IDs are globally unique and permanently claimed**, even after the project is deleted. `gcp-de-course` — the id used by this course's simulator — is one you must avoid, and `gcloud projects create` will refuse an id someone else has ever used. Append a random or personal suffix and check availability first with `gcloud projects describe YOUR_CHOSEN_ID 2>/dev/null`.

---

## 💡 Production Notes

- **Encode location in resource names.** `raw-events-us-central1` prevents a whole class of "which bucket is this?" errors at 2 a.m. The course project follows this convention with `raw-events-us-central1`, `curated_us-central1` and `events-us-central1`.
- **Create buckets with `--uniform-bucket-level-access` and enforce it with an organization policy.** Uniform bucket-level access disables per-object ACLs, which removes an entire family of confusing "why can my service account not read this object?" bugs.
- **Set a default region and zone per project, but always pass `--region` explicitly in scripts.** `gcloud config set compute/region` is a convenience for humans; scripts that depend on it break on a different machine.
- **Pin BigQuery datasets and Cloud Storage buckets deliberately, and never move them.** Location cannot be changed after creation for most resources. To relocate, you copy data and recreate the resource, then re-point consumers — plan for that as a migration project, not a rename.
- **Use folders for policy inheritance, not folders for tidiness.** The moment a folder exists to enforce an org policy or a shared IAM binding, it is earning its keep. A folder that only groups projects is a folder you will have to explain in an audit.
- **Remember the free tier is regional.** The always-free Compute Engine and Cloud Storage allowances apply only in `us-central1`, `us-east1` and `us-west1`. A lab environment in `europe-west4` will generate a bill.
- **Quotas are regional and project-scoped.** A quota limit of 0 for a service in your region means "not available", not "fix your permissions". `gcloud compute regions describe REGION` shows the quota limits and usage.
- **Do not rely on Cloud Shell for anything you cannot re-run.** It is ephemeral and single-session. Keep all commands in a repository and run them from a workstation or CI where the credential is explicit.

---

## 🔑 Key Takeaways

- A **zone** is an independent failure domain; a **region** is at least three zones; a **multi-region** is data replicated across regions. Durability mechanisms differ per resource — Cloud Storage is durable by design, a zonal Compute Engine disk is not.
- The hierarchy is **organization → folder → project → resource**, and IAM bindings plus organization policies inherit **strictly downward**.
- **Explicit DENY beats every ALLOW**, which is the only way to carve an exception out of a broad inherited grant.
- **Project IDs are immutable, globally unique and never recycled; project names are display labels and mutable.** Never derive an ID from a name.
- **Buckets live in a single global namespace**, unlike projects.
- Resource placement has **three axes** — latency, residency, cost — and legal residency wins over both.
- The cheapest region is usually `us-central1`, but the always-free allowances apply only in `us-central1`, `us-east1` and `us-west1`.
- **Check service availability in the region before choosing it.** Preview and restricted services carry no meaningful SLA.
- Use **Cloud Shell** for CLI work, **Cloud Editor** for authoring, and a **repository** for anything repeatable. The browser is a convenience, not a system of record.

---

## 📚 Practice Exercises

1. Run `python project/local_runner.py --regions` and identify every service that is preview or restricted in at least one region. For each, write one sentence on why you would not build a production pipeline on it.
2. Write a script that imports `service_catalog` and prints the zones for every region using `zones_in(region)`. Then explain in your own words why a zonal Compute Engine instance is a worse availability choice than a regional persistent disk, and what you would deploy alongside it.
3. Run `python project/local_runner.py --run` and draw the resource tree on paper. Label each resource with its service id from the catalogue. Then propose a folder/project layout for the same resources split across `prod` and `dev`, and say which bindings you would move up to the folder level.
4. Using `iam_policy.evaluate`, write a script that proves a binding on `projects/p/buckets/b` does **not** apply to `projects/p/buckets/b/objects/o` via that path, but that a binding on `projects/p` does. Explain why `projects/p/buckets` is not a valid IAM scope.
5. Create a real GCP project with a globally unique id, then create a Cloud Storage bucket in it named after the project. Attempt to create the same bucket name in a second project and explain the error using the global-namespace rule. Delete the first bucket and note whether the name becomes reusable.
6. Run `gcloud compute zones list --filter="region eq us-central1"` and compare it with `gcloud compute zones list --filter="region eq australia-southeast1"`. Explain why assuming every region has three zones with the same letters is unsafe, and how that assumption breaks autoscaling configuration.
7. Pick a client scenario: an EU-based retailer whose data must remain in the EU, whose users are in Frankfurt and Dublin, and whose budget is tight. Choose a region, justify it against all three axes, and name two services you would *avoid* there because of availability.
8. Design a folder hierarchy for an organisation with three teams (data engineering, data science, business analytics) and three environments (prod, staging, dev). State where you attach IAM bindings, where you attach org policies, and where the budget alerts live. Explain what breaks if you instead put all nine projects in one folder.

---

## 📖 Further Reading
- [Cloud Locations](https://cloud.google.com/about/locations)
- [Resource Hierarchy](https://cloud.google.com/resource-hierarchy/docs/overview)
- [Managing Resource Hierarchies](https://cloud.google.com/resource-hierarchy/docs/managing-hierarchies)
- [Project IDs and Names](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Cloud Storage Bucket Naming Guidelines](https://cloud.google.com/storage/docs/bucketnaming)
- [Cloud Shell](https://cloud.google.com/shell/docs)
- [Best Practices for Resource Location](https://cloud.google.com/resource-manager/docs/best-practices-resource-locations)
