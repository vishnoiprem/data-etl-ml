# Governance, Security and ML — Interview Questions

## 🎯 How to use this file

Fourteen questions covering Modules 7 and 8: Sensitive Data Protection, compliance and data residency, encryption including CMEK, Looker Studio and BI, ML fundamentals, prebuilt and AutoML models, custom training on Vertex AI, and BigQuery ML. The through-line is that **governance is a pipeline stage, not a document** — a control that is not automated is a control that does not exist.

## Questions

### Q1. What does Sensitive Data Protection do, and how does it fit into a data pipeline?

**Answer.** DLP discovers sensitive data in your data and either inspects it (classifies and reports) or de-identifies it (redacts, masks, tokenises, formats it). In a pipeline it belongs at two points: on ingest to detect and route PII, and before serving to prevent it leaking into a downstream system.

**Mechanism.** You define a **template** with **info types** — the built-in detectors (email address, credit card, phone, name, address, IP address) or custom ones you define with regular expressions. An **inspect** job returns findings; a **de-identify** job transforms the data. DLP is character-aware, which matters: it will not flag `1234-5678-9012-3456` if you have only written a loose digit pattern.

**Trade-off.** DLP is billed per inspected byte after a monthly free allowance ($0.10/GB in the model), and running it over the whole estate on every load is expensive. Regex-based detection is free and far less accurate — the course shows `looks_like_email` as the naive alternative.

**In practice.** I use DLP with custom info types for the fields that matter to my business (a customer reference, a national ID format), and I put the de-identify step in the curated layer — so the raw layer keeps the fidelity and the curated layer is safe to share. Detection on ingest is a filter; de-identification on publish is the control.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import looks_like_email, redact_pii

print("naive regex detector:", looks_like_email("ana.silva@example.com"))
print("naive redaction:", redact_pii("ana.silva@example.com"))
print("keeps last 4 chars only — but DLP can tokenise, which preserves joins")
```

---

### Q2. Why is a regex a poor substitute for a real detection service?

**Answer.** A regex matches a *shape*, not a *meaning*. It finds things that look like PII and misses things that are PII, and both errors are expensive in opposite directions.

**Mechanism.** The course's `looks_like_email` is a three-part pattern: `^[^@\s]+@[^@\s]+\.[^@\s]+$`. It flags `not-an-email@x.y` and misses `anna.silva at example dot com`, `a@localhost`, and an obfuscated address. More importantly, it cannot distinguish a *real* personal identifier from a *business* one — a support ticket's `orders@acme.com` is not PII in the sense the regulation cares about.

**Trade-off.** Regex is instant, free, deterministic and reviewable. DLP is accurate, context-aware, customisable and costs money per byte.

**In practice.** I use a regex as a *fast pre-filter* to decide what to send to DLP, and DLP as the authority. And I use DLP's **tokenisation** rather than redaction when the data must stay joinable — tokenisation preserves referential integrity across tables, while redaction destroys it. The course's `redact_pii` demonstrates the naive case: `****************.com` is useless for joins.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import looks_like_email, redact_pii

cases = [
    "ana.silva@example.com",
    "not-an-email@x.y",
    "a@localhost",
    "anna.silva at example dot com",
]
for value in cases:
    print(f"{value!r:<38} email={looks_like_email(value)}")

print()
print("redacted:", redact_pii("ana.silva@example.com", keep_last=4))
print("note: a tokenised value would still be joinable")
```

---

### Q3. What are the main de-identification techniques, and when do you use each?

**Answer.** Four main techniques: **redaction** (remove entirely), **masking** (replace characters, keep shape), **tokenisation** (replace with a surrogate key that stays consistent), and **format-preserving encryption** (encrypt into the same format). Choose based on whether the data must remain usable downstream.

**Mechanism.** Redaction destroys utility — the field is gone. Masking keeps the format but not the value, so a card number stays 16 digits. Tokenisation replaces the value with a deterministic surrogate, so the same input always yields the same token and joins still work — that is the property that makes it the right choice for analytics. Format-preserving encryption keeps the shape *and* the reversibility.

**Trade-off.** Every technique is a one-way door for the original value. Tokenisation needs a token vault that you protect as carefully as the data itself, and a compromise of the vault re-identifies everything.

**In practice.** My choice: tokenisation for identifiers you must join on (customer ID, email), masking for fields where only the format matters (partial card numbers for display), redaction only when the field has no analytical value at all. And I keep the mapping in a separate project with tighter IAM and CMEK, never alongside the data.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import redact_pii

for value in ("4111111111111111", "ana.silva@example.com", "short"):
    print(f"{value!r:<28} -> {redact_pii(value, keep_last=4)!r}")
```

---

### Q4. What is data residency, and how do you enforce it on GCP?

**Answer.** Data residency is the requirement that data stays within a specific geography. You enforce it by choosing the right locations, restricting which locations are permitted, and applying IAM so nobody can read across the boundary.

**Mechanism.** Three layers. **Location choice**: buckets, BigQuery datasets, Spanner instances and Compute Engine instances all have a location, and it is immutable for most of them — you cannot move a bucket between regions. **Org policy**: `constraints/gcp.resourceLocations` prevents a resource from being created outside the approved list. **IAM**: even with data in `europe-west1`, a global `roles/bigquery.dataViewer` on the project would let a US-based engineer read it.

**Trade-off.** Residency constrains your architecture. A multi-region dataset for global analytics may be legally impossible; a single-region warehouse means users outside the region pay a latency penalty or you replicate, and the replica is subject to the same residency rules.

**In practice.** I treat residency as a *project design constraint*, not a setting. Separate projects per jurisdiction, an org policy on locations that makes the wrong thing impossible to create, and IAM scoped so the data engineers in another region genuinely cannot read the dataset. The course's catalog shows how real the placement problem is — BigLake is preview in `southamerica-east1` and unavailable in `southamerica-east1` for some services, so a naive "one global deployment" fails on availability as well as on law.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, services_available_in

print("us-central1:", len(services_available_in("us-central1")), "services")
print("europe-west1:", len(services_available_in("europe-west1")), "services")
print("southamerica-east1:", len(services_available_in("southamerica-east1")), "services")
print()
print("Datastream restricted in:", SERVICES["datastream"].availability.restricted)
```

---

### Q5. What is data sovereignty, and how does it differ from residency?

**Answer.** Residency is about *where the data is stored*. Sovereignty is about *who controls it* — the jurisdiction's laws, the operator's ability to access it, and whether a foreign government can compel disclosure.

**Mechanism.** The technical controls are the same (locations, IAM, CMEK), but sovereignty adds questions that no GCP setting answers on its own: which legal entity operates the service, under which jurisdiction's law, and does the provider have access to the data? Control of the *encryption key* is the strongest technical lever you have, because a key the provider cannot reach is a key a compelled request cannot obtain.

**Trade-off.** Sovereignty-hard architectures (customer-managed keys in a customer-controlled key ring, separate projects, restricted access) add operational complexity and cost, and they constrain how much of the managed platform you can use.

**In practice.** The question I ask the legal team first is: *is the threat model a subpoena to us, or a subpoena to the cloud provider?* If the answer is the latter, CMEK with keys in a separate project under a different corporate entity is the meaningful control. If it is the former, strict IAM and audit logging are enough. I would never answer that question without the legal team — it is not an engineering decision.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["sensitive-data-protection"]
print(f"{service.name}: {service.summary}")
print("resources:", service.key_resources)
print("regions:", len(service.availability.available))
```

---

### Q6. What is encryption at rest, in transit and in use — and what does GCP do by default?

**Answer.** At rest means stored on disk; in transit means moving between services; in use means being processed by a service that could theoretically see plaintext. GCP encrypts **at rest by default** with Google-managed keys and **in transit by default** with TLS.

**Mechanism.** At rest, Google-managed keys are used and rotated automatically; you can supply your own key with CMEK, which makes the key lifecycle *your* responsibility — you can revoke it, which makes the data unreadable. In transit, TLS 1.2+ is used for API calls and inter-service traffic. In use, Google protects data in its own processing systems with additional controls, but a managed service that processes your data does technically handle plaintext — which is why some regulated workloads use dedicated confidential computing.

**Trade-off.** CMEK gives you control, revocation and audit; it also gives you the key's availability problem — if you lose the key, the data is gone. And it adds a permission surface and a KMS dependency to every service.

**In practice.** Google-managed keys by default; CMEK for anything under a compliance scope that requires it, with the key in a separate project, versioned, and with a documented rotation and revocation procedure. The critical rule: **the key must live in a different project from the data**, or the compromise of the data project is the compromise of the key too.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("cloud-storage", "bigquery", "cloud-sql", "cloud-spanner"):
    service = SERVICES[service_id]
    print(f"{service.name:<16} {service.summary}")
```

---

### Q7. What is CMEK, and what breaks when you adopt it?

**Answer.** CMEK is Customer-Managed Encryption Keys: you create the key in Cloud KMS and point a service at it, so the key's lifecycle, rotation and revocation are yours. What breaks is that you now own availability.

**Mechanism.** You create a **key ring** and a **key**, then grant the *service's service account* (for example the BigQuery service agent) the `cloudkms.cryptoKeyEncrypterDecrypter` role on the key. The service encrypts the data with a key-encryption-key derived from your key. When you **disable** or **destroy** the key version, the data encrypted under it becomes permanently unreadable — that is the point, and it is also the hazard.

**Trade-off.** CMEK gives you the ability to revoke access to data that is already stored, which no other control offers. It also means a KMS outage becomes a data outage, a mistaken key disable becomes data loss, and the permission graph grows by several edges.

**In practice.** I enable CMEK on the buckets and datasets that hold regulated data, keep the key ring in a dedicated security project, separate the key admin from the data admin so no single person can read the data, and test the revocation procedure on a non-critical bucket before trusting it. And I set an alert on key version state, because a disabled key version is the most expensive possible mistake.

**Failure story.** A team enabled CMEK, then rotated by creating a new key version. The service still pointed at the old version, and a routine cleanup job — written to delete old key versions — destroyed the version still in use. The bucket was unreadable for six hours while the version was restored from the key's schedule, and the data past that point was gone. The lesson: **key rotation and key destruction are different operations, and they need different approvals.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import ROLE_SUMMARY, ROLES

print(ROLE_SUMMARY["roles/storage.admin"])
print("permissions in roles/storage.admin:", len(ROLES["roles/storage.admin"]))
```

---

### Q8. Which compliance frameworks does GCP support, and how do you actually evidence compliance?

**Answer.** GCP supports SOC 1/2/3, ISO 27001, ISO 27017/27018, PCI DSS, HIPAA, FedRAMP and GDPR readiness. Evidence comes from the shared-responsibility model: Google evidences the *infrastructure*, and you evidence the *configuration*.

**Mechanism.** The shared-responsibility boundary for IaaS is roughly: Google secures the physical infrastructure, the hypervisor, the networking and the facility; you secure the operating system, the middleware, your application and your data, plus the IAM configuration that gives access to it.

**Trade-off.** A certification tells you about Google's controls, not about your project. A SOC 2 report on Google Cloud says nothing about whether your Cloud SQL instance has public IPs and a weak password — that is your part of the model, and it is the part auditors check.

**In practice.** I use the **Audit Logs** service as the evidence backbone — Admin Activity, Data Access, System Event and Policy Denied logs, exported to a locked sink in a separate project. Then I run a configuration audit against CIS benchmarks. The evidence question ("show me who read this table in March") is answered by a log export, not by a screenshot.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from iam_policy import Principal, Policy, Binding, evaluate, ROLE_SUMMARY

print(ROLE_SUMMARY["roles/bigquery.dataViewer"])
print(ROLE_SUMMARY["roles/bigquery.jobUser"])
print("a dataViewer grant implies the ability to read every row:")
print("  bigquery.tables.getData ->", "bigquery.tables.getData" in __import__("iam_policy").ROLES["roles/bigquery.dataViewer"])
```

---

### Q9. What is Looker Studio, and when would you use Looker instead?

**Answer.** Looker Studio is a free, browser-based BI and dashboarding tool that connects to BigQuery, Sheets and many other sources. Looker is the governed enterprise BI product with a semantic layer, and it is a separate product with its own cost per user.

**Mechanism.** Looker Studio is built around a **report** containing **data sources** and **charts**. When the source is BigQuery, the connector either runs the query live or reads a **materialised view** or a saved result. The governance model is basic — sharing is at the report and folder level.

**Trade-off.** Looker Studio is free and fast to build but its permission model is coarse: a viewer of a report over a BigQuery table sees the rows the query returns, and the access control is on the *data source*, not per-field. Looker adds a semantic layer where metrics are defined once, explored consistently, and governed.

**In practice.** I use Looker Studio for exploration, light dashboards and stakeholder read-only views — because it is free and the audience is broad. I use Looker when there is a governed metric definition that must be consistent across the company, and I use a BigQuery view or a semantic layer when the metric must be right rather than consistent.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("looker-studio", "looker"):
    service = SERVICES[service_id]
    print(f"{service.name}: {service.summary}")
    print(f"   pricing: {service.pricing_model}")
    print(f"   resources: {service.key_resources}")
```

---

### Q10. What is a BI semantic layer, and why does it matter?

**Answer.** A semantic layer is a governed definition of your business metrics, sitting between the raw data and the dashboards, so that "monthly active customers" means exactly one thing across every tool.

**Mechanism.** In Looker, a **model** defines tables and their relationships, and an **explore** exposes a curated set of fields and dimensions. In a dbt or Dataform project, the equivalent is a set of modelled tables with documented definitions and tests. Both serve the same purpose: the metric is computed once, in version-controlled code, and every consumer reads the same definition.

**Trade-off.** A semantic layer costs engineering time up front and adds a layer that consumers must learn. Without it, every dashboard author writes their own version of "active customer" and the numbers disagree.

**In practice.** I insist on it as soon as two dashboards exist. The failure it prevents is worse than the cost: two teams present different revenue numbers to the same executive in the same meeting, and the argument about whose number is right consumes more trust than the metric itself. The course's `EXPECTED_SUMMARY` is the smallest possible version of this idea — one place defines the aggregate, and everything else reads it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_events, ingest_events, EXPECTED_SUMMARY

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)
summary = aggregate_events(accepted)

# One definition, consumed everywhere.
print("single source of truth:", EXPECTED_SUMMARY == summary)
for region in sorted(summary):
    print(f"  {region}: {summary[region]['revenue_eur']:,.2f} EUR")
```

---

### Q11. Explain supervised versus unsupervised learning, and where each fits in a data pipeline.

**Answer.** Supervised learning learns a mapping from labelled examples — you provide the answer and the model learns to predict it. Unsupervised learning finds structure in unlabelled data — clusters, anomalies, latent factors — without being told what to look for.

**Mechanism.** Supervised learning needs a labelled training set, a **feature** vector per example, a **loss function** measuring prediction error, and an optimiser that minimises it. Unsupervised learning optimises an objective such as within-cluster variance or reconstruction error, with the structure chosen by you.

**Trade-off.** Supervised learning gives you a metric you can test against a held-out set. Unsupervised learning gives you structure but **no ground truth** — you cannot measure whether the clusters are meaningful, only whether they are stable and useful.

**In practice.** In a data-engineering context, supervised learning fits where you have a label — fraud detection, churn prediction, demand forecasting — and the pipeline's job is to produce a trustworthy training set with no leakage. Unsupervised fits anomaly detection on unlabelled logs, where the output is a score per row that a human then labels. The pipeline concern in both is **skew**: the training data must reflect the serving data, and temporal leakage — a feature computed from data that did not exist at prediction time — is the most common reason a model works offline and fails in production.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import ingest_events, validate_event

# A supervised label needs a reliable source.
lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

labelled = [row for row in accepted if row["event_type"] in ("order", "refund")]
print(f"rows with a usable label: {len(labelled)} of {len(accepted)}")
print("label classes:", sorted({row["event_type"] for row in labelled}))
```

---

### Q12. When would you use a prebuilt or AutoML model instead of training your own?

**Answer.** Use a prebuilt model when the task is one Google already solved well — vision, speech, translation, text moderation — and use AutoML when you have labelled data but do not want to tune hyperparameters yourself.

**Mechanism.** Vertex AI's **pre-trained models** (Vision API, Speech-to-Text, Translation, Natural Language) are served APIs with no training. **AutoML** (Vertex AI AutoML for tabular, image, text, video) takes your labelled dataset, searches the model space for you, and exports the winner to Cloud Storage or deploys it to an endpoint.

**Trade-off.** Prebuilt models give you a quality baseline in an afternoon and a black box you cannot change. AutoML gives you a model that fits your data but spends real money on the search — and the search result is often only slightly better than a well-tuned baseline, so the engineering effort can exceed the gain.

**In practice.** I start with the prebuilt model to get a baseline and a working pipeline, then decide whether the delta is worth it. The real work is not the model — it is the **evaluation set** and the **serving path**. A model with no evaluation set is not deployed, and a model with no serving path is not useful.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import VERTEX_AI_TRAINING_PER_NODE_HOUR, estimate

print("training node-hour:", VERTEX_AI_TRAINING_PER_NODE_HOUR)
print(estimate("vertex-ai", training_node_hours=4, monthly=False))
```

---

### Q13. What does custom training on Vertex AI actually involve, and how do you operationalise a model?

**Answer.** Custom training is running your own training code on Vertex AI's managed infrastructure — a training pipeline with prebuilt containers or your own image, running on managed compute or a Kubernetes or AI Platform job.

**Mechanism.** A Vertex AI **pipeline** is a DAG of steps: preprocessing, training, evaluation, model registration, deployment. Models are written to the **Vertex AI Model Registry**, and **endpoints** serve them — a managed, autoscaling prediction service with its own versioning and traffic splitting.

**Trade-off.** Custom training gives you full control over the algorithm, the features and the hyperparameters, and it costs real money — $3.67 per training node-hour in the model, which is a single-digit-dollar-per-minute number that adds up over many experiments. Managed operations (a retraining pipeline, an endpoint, monitoring) are also your responsibility once you leave the prebuilt path.

**In practice.** The three things that decide whether a model is actually in production: a **feature pipeline** that produces the same features at training and serving time, a **drift and skew monitor** on the endpoint, and a **retraining trigger** with an evaluation gate that blocks a bad model from reaching users. Without the feature pipeline, training-serving skew silently destroys the model — the training features are computed from a batch pipeline, the serving features from a streaming one, and they differ.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["vertex-ai"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)
```

---

### Q14. What is BigQuery ML, and when is it the right choice?

**Answer.** BigQuery ML lets you train and serve models with SQL inside the warehouse — `CREATE MODEL`, `SELECT * FROM ML.PREDICT(...)` — using BigQuery data directly, with no data movement.

**Mechanism.** You train with a `CREATE MODEL` statement specifying the model type (`LOGISTIC_REGRESSION`, `LINEAR_REG`, `KMEANS`, `DNN_CLASSIFIER`, and so on), the feature columns, the label column and the training options. Inference is a query — `ML.PREDICT` for batch, and you can also create a **remote model** over a Bigtable endpoint for online serving. The training data never leaves BigQuery.

**Trade-off.** BigQuery ML is remarkably good for the model classes it supports and for tabular data that is already in BigQuery — the whole path from data to prediction is one SQL statement, which eliminates an entire class of pipeline. It is not a general ML platform: no custom training code, no custom architectures, no hyperparameter search of any sophistication, and inference is billed as a query.

**In practice.** I use BigQuery ML for **baseline models and simple production predictors** — a propensity score, a demand forecast, a churn classifier over a table that is already there. The moment the model needs custom features, custom loss, or a deep architecture, I move to Vertex AI. And I always compare against a trivial baseline — if a linear model over two features does not beat "predict the mean", the model is not earning its complexity.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES
from cost_model import estimate

service = SERVICES["bigquery-ml"]
print(f"{service.name}: {service.summary}")
print("pricing:", service.pricing_model)
print("resources:", service.key_resources)
print()
print("BigQuery ML rides on BigQuery compute:")
print(estimate("bigquery", scanned_tb=1.0))
```

---

## 📚 Related chapters

- [7.1 — Sensitive Data Protection](../chapters/27-sensitive-data-protection.md)
- [7.2 — Compliance, Residency & Encryption](../chapters/28-compliance-residency-and-encryption.md)
- [7.3 — Looker Studio & BI](../chapters/29-looker-studio-and-bi.md)
- [8.1 — ML Foundations on GCP](../chapters/30-machine-learning-foundations.md)
- [8.2 — Prebuilt & AutoML Models](../chapters/31-prebuilt-and-automl-models.md)
- [8.3 — Custom Training & Vertex AI](../chapters/32-custom-training-and-vertex-ai.md)
- [8.4 — BigQuery ML](../chapters/33-bigquery-ml.md)
- [8.5 — End-to-End Capstone](../chapters/34-end-to-end-capstone.md)

## 📖 Further Reading

- [Sensitive Data Protection documentation](https://cloud.google.com/sensitive-data-protection/docs)
- [Data residency on Google Cloud](https://cloud.google.com/security/compliance/data-residency)
- [Encryption at rest in Google Cloud](https://cloud.google.com/security/encryption-at-rest)
- [Cloud KMS overview](https://cloud.google.com/kms/docs)
- [BigQuery ML documentation](https://cloud.google.com/bigquery/docs/bqml-introduction)
