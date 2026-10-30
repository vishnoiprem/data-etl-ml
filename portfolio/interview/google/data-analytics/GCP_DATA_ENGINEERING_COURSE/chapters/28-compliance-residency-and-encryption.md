# 7.2 — Compliance, Residency & Encryption

> **Section 7 · Governance, Security & BI · Lecture 7.2 · 8:00**

## 🎯 What you will learn

- Data residency: the difference between data **stored in** a region and data **processed in** a region
- Regional, multi-regional, and dual-regional placement, and which one satisfies which obligation
- The residency regulatory regimes: GDPR, and Singapore's MAS TRM / PDPA
- Legal and regulatory compliance: HIPAA, PCI DSS, SOC 2, FedRAMP — and what Google's certification actually means for *you*
- The encryption model at rest: Google's default keys versus **CMEK** via Cloud KMS and Cloud HSM
- The KMS key hierarchy, key rings, key versions, and **who can actually decrypt**
- Encryption in transit: TLS everywhere, and the Private Service Connect / VPC Service Controls story
- The shared-responsibility split, stated honestly
- A practical checklist for shipping a regulated workload

---

## 🧠 Concept

### Residency: the three distinct questions

Most residency mistakes come from treating "residency" as one question. It is three, and they have different answers and different tools.

> **1. Where is the data stored?**
> **2. Where is the data processed (compute)?**
> **3. Where are the backups and the control plane?**

**"Stored in" versus "processed in"** is the distinction that catches most people.

- **Storage residency** is where the bytes at rest live. This is what you control with the `location` of a Cloud Storage bucket, the `region` of a BigQuery dataset, and the region of a Cloud SQL instance.
- **Processing residency** is where the CPU that reads and transforms those bytes runs. A BigQuery query against a `europe-west4` dataset runs in `europe-west4` — good. But a Dataflow job in `us-central1` that reads that dataset has *moved* the data to `us-central1` for processing, and the transfer crossed a border.
- **Backup residency** is where the replicas live. A regional Cloud Storage bucket replicates within its region. A multi-regional bucket replicates across regions — which means your `US` bucket has a copy in `us-east1` and `us-west1`, and if the regulator's requirement is "all data in the EU", a multi-region bucket labelled `EU` is fine but a `US` bucket is not.

**The operational consequence:** *placing your storage correctly while running your compute somewhere else does not satisfy a residency requirement.* And this is exactly what happens when a team puts a bucket in `europe-west4` and then runs a Composer DAG or a Dataproc cluster in `us-central1` to process it, because that is where the company's default region is.

### Placement: regional, multi-regional, dual-regional

| Placement type | Where it lives | Latency | Use for |
|---|---|---|---|
| **Regional** (`europe-west4`) | One region | Lowest | Residency requirements, lowest latency |
| **Multi-regional** (`EU`, `US`) | Two or more regions in a continent | Higher | High availability across a geography |
| **Dual-regional** (`nam4`, `eur4`) | Two named regions, e.g. `us-east1` + `us-west1` | Medium | Tight RTO/RPO across two specific regions |
| **Global** (BigQuery, Cloud Storage global buckets) | Multiple continents | Highest | Genuinely global data |

**Multi-regional and dual-regional are availability choices, not residency choices.** This is the key insight:

- A multi-regional `EU` bucket **does** satisfy an EU residency requirement — all its replicas are in EU regions.
- A multi-regional `US` bucket **does not**, even though it has two replicas.
- Choosing `US` because it is "more available" is a residency violation if your data is EU citizens' data.

**The critical caveat about `US` and `EU` multi-regions:** they are not single countries. `EU` covers the EEA plus the UK (as of the current configuration). If your regulator requires data in **Germany** specifically, `EU` does not satisfy it — you need `europe-west3` (Frankfurt) or `europe-west4` (Amsterdam), regionally.

**BigQuery has a specific nuance worth knowing.** A BigQuery dataset is either regional or multi-regional (`US`, `EU`). BigQuery's processing happens in the dataset's location. **BigQuery also caches query results**, and the cache respects the dataset location. But BigQuery's control plane is global — the metadata, the job graph, and the billing live in the US. No customer data is stored there, but a regulator asking "is any of my data outside the EU" will ask about metadata too. The answer is that query metadata (query text, job names) is not customer data, but **query text can contain customer data** if you inline literal values. The mitigation is to use parameters and table references, not literals.

### The residency regulatory regimes

**GDPR (European Union / EEA)**

The operative concepts:

- **Personal data** is broader than "PII fields". It is any information relating to an identified or identifiable person. A `user_id` is personal data. A `device_id` is personal data. An IP address is personal data (with the caveat that the Court of Justice of the EU held in *Breyer* that an IP address is personal data when combined with additional information).
- **Special category data** (Article 9) — health, biometric, genetic, political opinions, trade union membership, sex life, sexual orientation. This needs an explicit lawful basis, not just a lawful basis.
- **The key articles for a data engineer:**
  - **Article 5** — the principles: lawfulness, fairness, transparency; purpose limitation; data minimisation; accuracy; storage limitation; integrity and confidentiality; accountability.
  - **Article 25** — data protection by design and by default. This is the engineering article.
  - **Article 30** — records of processing activities. Your data catalog is part of this.
  - **Article 32** — security of processing. Encryption, pseudonymisation, and access control are named explicitly.
  - **Article 33/34** — breach notification, 72 hours to the supervisory authority.
- **The residency question for GDPR:** GDPR does **not** require EU storage for EU citizens' data. It requires that transfers outside the EEA have an adequacy decision, appropriate safeguards (SCCs), or another lawful mechanism. **"EU citizens" is also not the test** — the test is residency of the *data subject* and the *establishment* of the controller or processor.

**This is the most common misconception in the field**, and it is worth stating bluntly: *GDPR is not a data-residency law.* GDPR does say that transfers to a third country without an adequacy decision require appropriate safeguards, and that the transfer must be assessed (the Schrems II "supplementary measures" analysis) — and if you can access the data from the third country, that is itself a transfer.

But the engineering consequences are real:
- If your data must not leave the EEA at all (a contractual or sector-specific requirement layered on top), you place everything in an EU region.
- If GDPR residency per se is the requirement, EU storage is the simplest way to satisfy it, and it is what most organisations do anyway.
- **Data minimisation (Article 5(1)(c)) has a direct architectural consequence:** do not copy columns into your warehouse because you might need them. The minimal dataset is both the compliant dataset and the cheap one.

**Singapore: MAS TRM and the PDPA**

Two instruments matter, and they are frequently confused:

**The Personal Data Protection Act (PDPA)** — Singapore's general data protection law. Key features:
- **Consent, purpose and notification** are the core obligations. You must tell the individual what you are collecting and why.
- **Purpose limitation** — collect for a stated purpose, do not repurpose without fresh consent.
- **Protection Obligation** — reasonable security arrangements. This is where encryption and access control live.
- **Retention Limitation** — cease to retain once the purpose is served. This has a direct engineering consequence: **you need a deletion path**, and "we keep everything in BigQuery forever" is a PDPA problem.
- **Breach notification** — notify the PDPC and affected individuals when a breach is likely to cause harm.
- **Data portability** — on request, transmit data to another provider in a commonly used format.
- **Comparison obligation** — a data subject may ask you to compare data you hold about them with data held by another provider.
- **Consent in marketing and customer-facing purposes** — separate, explicit consent.

**The MAS Technology Risk Management Guidelines (TRM)** — the MAS-specific rules for banks and financial institutions in Singapore. The relevant requirements for a data platform:
- **Data classification** — you must classify your data by sensitivity (Public, Internal, Confidential, Restricted) and apply controls accordingly. This is a metadata-tagging exercise; Dataplex tag templates and Data Catalog tag templates exist precisely for this.
- **Data residency and cross-border transfer** — banks are typically required to keep certain customer information in Singapore. MAS's expectations for a financial institution are stricter than the PDPA baseline.
- **Encryption and cryptographic controls** — MAS requires that sensitive customer information be encrypted at rest and in transit, with key management under the institution's control. **This is where CMEK stops being optional.**
- **Access control, audit logging, and periodic review** — access must be reviewed on a defined cadence, and there must be an audit trail.
- **Cloud Third-Party Management (TPCM) Guidelines** — the risk assessment and contractual controls for using a cloud provider. MAS requires a documented assessment before onboarding a cloud provider, not after.

**The residency regimes, side by side:**

| | GDPR | Singapore PDPA | MAS TRM |
|---|---|---|---|
| **Instrument** | Regulation (EU law) | Act (Singapore statute) | Guidelines (MAS rules for FIs) |
| **Applies to** | Processing of EEA personal data | Personal data of Singapore individuals | Singapore-authorised financial institutions |
| **Storage location** | Not mandated | Not mandated | Often mandated by MAS expectations |
| **Key obligations** | Lawful basis, minimisation, security, rights | Consent, purpose, protection, retention, breach | Classification, encryption, access reviews, cloud vendor risk |
| **Engineering impact** | Minimise; encrypt; pseudonymise; delete on request | Delete on request; notify; secure | CMEK; classification tags; audit logs; periodic access review |

**The engineering takeaway that is the same across both regimes: you need three capabilities you may not have built yet.**

1. **Deletion.** A request to delete an individual's data must actually remove it — including from BigQuery partitions, from Cloud Storage objects, and from the dead-letter quarantine. This is the hardest one, and it is why the course pipeline's quarantine bucket deserves a lifecycle rule.
2. **Data minimisation.** Store what you need. The `region_reference.ndjson` reference table in the sample data is a good example — a lookup table of 50 rows is fine; copying the whole dimension into every event row is not.
3. **Auditability.** Who read what, when. Cloud Audit Logs plus a lineage graph plus a data catalog.

### Legal and regulatory compliance: what Google's certifications mean for you

This section exists because "we're on GCP, so we're HIPAA compliant" is a category error that causes real problems.

**The certifications Google holds:**

| Certification | What it says | What it does NOT say |
|---|---|---|
| **SOC 2 Type II** (and SOC 1, SOC 3) | Google's *own* controls are audited annually by an independent firm | Nothing about your configuration, your IAM, your code, or your data |
| **ISO 27001, 27017, 27018, 27701, 22301, 27002** | Google's ISMS is certified; 27017 is the cloud-specific control set | Nothing about your use of the platform |
| **PCI DSS** (Level 1 Service Provider) | Google's infrastructure is in scope for cardholder data | **You** are still responsible for your application, your configuration, and your handling of cardholder data |
| **HIPAA** (BAA available) | Google will sign a Business Associate Addendum; covered services are HIPAA-eligible | **You** must determine whether your workload is HIPAA-eligible, configure it correctly, and manage access |
| **FedRAMP** (High, Moderate, Moderate in some services) | Google's cloud is authorised for federal agencies | Your workload must be in an authorised region, use authorised services, and meet the control requirements — and FedRAMP authorisation does **not** extend to commercial workloads |
| **CSA STAR** | Google's cloud meets the Cloud Security Alliance's registry criteria | Same as SOC 2 — Google's controls, not yours |

**The shared responsibility model, stated precisely:**

```text
Google is responsible for:
  - The physical infrastructure: data centres, servers, power, cooling, networking
  - The virtualization layer and the hypervisor
  - The management plane of the services it operates
  - The patching of its own software
  - Availability, durability, and the security of the base platform

You are responsible for:
  - Your data: classification, residency, minimisation, retention, deletion
  - Your configuration: IAM, firewall rules, bucket policies, VPC-SC boundaries
  - Your code: what it does with the data, whether it logs it, whether it leaks it
  - Your identities: who has access, how it is granted, how it is reviewed
  - Your key management decisions: whether to use CMEK, and who holds the keys
  - Your monitoring and incident response
  - The correctness of your claims to your users and your regulator
```

**The compliance phrase that should worry you:** "Google is HIPAA eligible" means *Google's infrastructure is eligible*. It does not mean *your data on it is compliant*. Concretely, if a HIPAA-regulated dataset lands in a project where every engineer on a 40-person team has `roles/owner`, you are not compliant, no matter what the BAA says.

**What you must do to actually use these certifications:**

1. **Sign the BAA** (HIPAA) before putting PHI on GCP. No BAA, no compliance — this is a contractual gate, not a technical one.
2. **Use only HIPAA-eligible services** in the project's allow-list, and enforce it with an org policy.
3. **Configure the project correctly:** restricted IAM, no public buckets, VPC-SC if required, CMEK where required.
4. **Document your own controls** and produce your own evidence — access reviews, key rotation records, deletion logs.
5. **Do not use FedRAMP authorisation as a marketing claim** for a commercial workload. It is a government authorisation with specific scope, and misattributing it is a compliance failure in itself.

### Encryption at rest

**Google's default.** Every piece of persistent data on GCP is encrypted at rest by default with **Google-managed keys**. The details:

- Each service's storage layer encrypts before writing to disk. You cannot see the plaintext on the physical media.
- **The keys are managed by Google.** They are encrypted at rest themselves, with a hardware security module (HSM) in Google's key-management infrastructure.
- **Key rotation is handled by Google**, typically annually, without any action from you.
- **You cannot revoke Google's access** to your data through the key system, because you do not hold the key.

**This is a strong default and it is sufficient for most workloads.** The important question is not "is my data encrypted" — it is "**who can decrypt it, and can I prove that**".

**CMEK — Customer-Managed Encryption Keys** changes the answer. With CMEK:

- **You create the key** in Cloud KMS (or a Cloud HSM), and Google encrypts your data with *your* key.
- **Your data is unreadable without your key.** If you disable or delete the key version, the data encrypted with it is permanently inaccessible. There is no Google back door.
- **The key's permissions are your permissions.** Anyone with `cloudkms.cryptoKeyEncrypterDecrypter` on the key can decrypt. That means the key becomes part of your access-control model, and it is a very high-value target.
- **The key can be rotated**, and old versions can be disabled while the data remains readable with the new one. You decide the rotation schedule.

**The hierarchy, from the top down:**

```text
Organization
  └── Folder  (optional)
        └── Project
              └── Cloud KMS Key Ring
                    └── CryptoKey  (e.g. "bigquery-key")
                          └── CryptoKeyVersion  (1, 2, 3, ...)
                                └── Key material
```

- A **key ring** is a logical container for keys, and it lives in a **location**. **The key ring's location must match the resource's location.** You cannot create a key ring in `europe-west4` and use it to encrypt a BigQuery dataset in `us-central1`. This is the mechanism by which CMEK *enforces* residency — it is not a policy, it is a technical impossibility.
- A **CryptoKey** has metadata and versions.
- A **CryptoKeyVersion** holds the actual key material. Versions have a state: `ENABLED`, `DISABLED`, `PENDING_DESTROY`, `DESTROYED`, `DESTROY_SCHEDULED`.

**Who can decrypt — the critical question.** Getting CMEK right is not about turning it on. It is about controlling the key's IAM. There are three distinct permissions and they are not interchangeable:

| Permission | What it allows | Where it is needed |
|---|---|---|
| `cloudkms.cryptoKeyVersions.viewPublicKey` | Read the public key only | Encryption clients that need to encrypt but not decrypt |
| `cloudkms.cryptoKeyEncrypter` | Encrypt data with this key | The service writing the data (BigQuery, GCS) |
| `cloudkms.cryptoKeyEncrypterDecrypter` | **Encrypt AND decrypt** | Anyone who can read the plaintext back |

**The failure mode:** granting `cryptoKeyEncrypterDecrypter` to a human so they can "read the data", and thereby being able to decrypt every table protected by that key. A key with a broad decrypt role is worse than no CMEK, because it *looks* like control while actually delegating the authority.

**The correct pattern:** the *service* (BigQuery, Storage) holds `cryptoKeyEncrypter` to write. *Humans* do not hold the key at all — they read the data through the service, and the service's service account does the decryption. To let a human read a table, grant them BigQuery read access, not KMS access. **This is the whole design pattern of CMEK: it moves trust from the data plane to the key plane, without giving humans the key plane.**

**Cloud HSM** is the tier above Cloud KMS. It provides a FIPS 140-3 Level 3 hardware boundary for key generation and storage. It is required by some regulatory regimes and by some customers' internal policy, and it costs more. The escalation path is: **Google-managed keys → Cloud KMS (software) → Cloud KMS (HSM-backed)**.

**Regionality of keys.** Cloud KMS key rings are regional. A key in `europe-west4` is the key for `europe-west4` resources. For a multi-regional dataset, you use the corresponding multi-regional key ring, and Google handles the regional replicas of the key.

### Encryption in transit

**TLS everywhere.** Every GCP service-to-service and client-to-service connection is encrypted with TLS in transit. This is not optional and not configurable — it is the platform.

**The parts you must configure:**

- **Browser to service** — TLS for every console and API call.
- **Your application to the database** — Cloud SQL requires TLS unless you explicitly disable it. The `require_ssl` flag on a Cloud SQL instance is `ON` by default for PostgreSQL; for MySQL, `sslMode` should be `ENCRYPTED_ONLY` or `TRUSTED_CLIENT_CERTIFICATE`, not `DISABLED`.
- **Within a VPC** — VPC peering and Cloud Interconnect traffic is encrypted in transit by default. There is no option to turn it off.
- **Pub/Sub** — encrypted in transit and at rest by default; the publisher and subscriber service accounts must be in the same project (or the topic must be granted) for the service to use Google-internal encryption.
- **From on-premises to Cloud SQL** — use the Cloud SQL Auth Proxy, which wraps the connection in TLS, or Cloud SQL Auth Connector.

**Private Service Access and VPC Service Controls** are the two mechanisms that control *where* traffic goes, and they solve a different problem from encryption:

**Private Service Access (PSA)** gives a VPC a private IP range that Google-managed services (Cloud SQL, Memorystore, AlloyDB, and others) can be reached on. The traffic never leaves Google's network, and the service has no public IP. This is **network-level isolation**: the service is not reachable from the internet at all.

**VPC Service Controls (VPC-SC)** is the perimeter mechanism, and it is the one that matters for regulatory compliance. It lets you define a **service perimeter** — a boundary around a set of GCP resources and a set of allowed API call origins. Then:

- Resources inside the perimeter can only be accessed by identities whose origin is inside the perimeter.
- Requests from outside are **denied by default** and only allowed through explicit rules.
- **The key property: even a stolen credential cannot exfiltrate data out of the perimeter.** A service account with `storage.objects.get` on a bucket inside the perimeter, used from an attacker’s laptop outside the perimeter, is blocked. This is the control that stops the "compromised key exfiltrates the data" scenario — the one that CMEK alone does not solve, because the key's IAM is still project-scoped.

**The correct combination for a regulated workload:**

- **CMEK** controls *who holds the key*.
- **VPC-SC** controls *from where data can be read*.
- **IAM** controls *who can read*.
- **VPC-SC + CMEK together** are what let you say "even an administrator with project-wide IAM cannot read this data without also being inside the perimeter."

### The shared-responsibility split, applied to a data pipeline

Let us make this concrete with the course pipeline, because abstract shared-responsibility diagrams are not useful.

| Layer | Google | You |
|---|---|---|
| **Storage** | Encrypts the bucket at rest, handles key rotation, replicates within the region | Classify the data, decide the location, set the lifecycle, enforce retention, delete when required |
| **Compute** | Patches the runtime, isolates tenants, encrypts the hypervisor | Choose the runtime, configure it, patch your own images, write secure code |
| **Identity** | Provides IAM, logs every API call, supports MFA and conditional access | Decide who gets which roles, review them, remove them when people leave, use groups not individuals |
| **Keys** | Provides the HSM, key rotation for managed keys, the KMS API | Choose managed vs CMEK, define the key ring topology, control the key IAM, rotate and disable, **decide who can decrypt** |
| **Application** | Nothing — this is yours | Validate input, do not log PII, handle errors without leaking payloads, apply least privilege |
| **Monitoring** | Provides Cloud Audit Logs, Security Command Center, log sinks | Alert on them, triage them, act on them, keep the evidence for the auditor |
| **Residency** | Provides regional infrastructure and enforces that data stays in its region | Choose the region, verify that every derived resource — including compute — is in that region, and keep the evidence |

**The line that most often gets crossed:** the course pipeline's `reject_counts` and dead-letter path. When a malformed event is rejected, the raw row is written to a quarantine table. If that raw row contained a partial card number or an email address, the quarantine table is now a second, less-protected copy of the sensitive data. **That copy is yours.** It needs the same encryption, the same IAM, the same residency, and a retention policy that deletes it.

### A checklist for a regulated workload

Here is the checklist as an operational document, in the order you should actually do it.

**Placement**
- [ ] Every persistent resource is in a region that satisfies the residency requirement.
- [ ] Multi-regional and dual-regional choices are verified to be inside the required geography (not just "the right continent").
- [ ] Every **compute** resource that touches the data is in the same region. Check Composer, Dataproc, Dataflow, Data Fusion, Dataprep, and Cloud Run.
- [ ] Backups and replicas are in the permitted geography.
- [ ] The bucket's and dataset's `location` is recorded in the asset registry.

**Encryption**
- [ ] CMEK is enabled for the resources the policy requires (or the decision not to use it is documented).
- [ ] Every key ring is in the same region as the resource it protects.
- [ ] Key IAM is reviewed: the service has `cryptoKeyEncrypter`; **no human has `cryptoKeyEncrypterDecrypter`**.
- [ ] Key rotation is scheduled and the schedule is monitored.
- [ ] Disabled key versions are cleaned up.

**Access**
- [ ] No human holds `roles/owner` on a production project. Owner is for break-glass, held by a small group.
- [ ] Access is via groups, not individual accounts.
- [ ] Access reviews run on a defined cadence and the results are recorded.
- [ ] Service accounts have no keys where workload identity or service account impersonation will do.
- [ ] VPC-SC perimeters are configured for the sensitive data, with the allowed origins enumerated deliberately.

**Data**
- [ ] Data is classified, and the classification is stored as tags on the assets (Dataplex tag templates, Data Catalog tag templates).
- [ ] Minimisation has been applied: columns that are not needed are not copied.
- [ ] A deletion path exists and has been **tested** — including from the quarantine path.
- [ ] Retention/lifecycle rules are configured and the deletion is verified, not assumed.
- [ ] Logging does not contain raw payloads. The pipeline's `redact_pii` and the DLP templates are the models here.
- [ ] A DLP inspection has run over the data and the findings have been triaged.

**Evidence**
- [ ] Cloud Audit Logs are exported to a sink the data owners cannot delete from.
- [ ] The lineage graph (Dataplex / BigQuery column-level lineage) is populated.
- [ ] The records of processing activities (GDPR Article 30) are maintained.
- [ ] The vendor risk assessment for the cloud provider is documented (MAS TPCM for a Singapore FI).
- [ ] The BAA, or the equivalent contractual instrument, is signed before PHI lands.

---

## 🛠️ Hands-On

### Lab 1 — Regional availability as a residency constraint

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import REGIONS, get_service, regions_for

# The EU regions in the course catalogue.
EU_REGIONS = [r for r in REGIONS if r.startswith("europe-")]
APAC_REGIONS = [r for r in REGIONS if r.startswith("asia-") or r.startswith("australia-")]
SG_REGION = "asia-southeast1"

print(f"EU regions      : {', '.join(EU_REGIONS)}")
print(f"APAC regions    : {', '.join(APAC_REGIONS)}")
print()

# A service is residency-eligible in a region only if it is available there.
CANDIDATES = ["cloud-storage", "bigquery", "cloud-sql", "data-fusion",
              "dataprep", "dataplex", "data-catalog", "looker-studio",
              "sensitive-data-protection"]

print(f"{'service':<28} {'EU':>6} {'SG':>6}")
print("-" * 42)
for service_id in CANDIDATES:
    service = get_service(service_id)
    available = regions_for(service_id)
    eu_ok = all(r in available for r in EU_REGIONS)
    sg_ok = SG_REGION in available
    print(f"{service_id:<28} {'yes' if eu_ok else 'NO':>6} {'yes' if sg_ok else 'NO':>6}")
print()

print("A 'NO' in the EU column means the workload cannot be run entirely")
print("inside the EU with that service. That is a design constraint, not")
print("a paperwork problem: the compute has to live somewhere.")
```

Expected output:

```text
EU regions      : europe-west1, europe-west2, europe-west4
APAC regions    : asia-south1, asia-southeast1, asia-northeast1, australia-southeast1

service                          EU     SG
------------------------------------------
cloud-storage                   yes    yes
bigquery                        yes    yes
cloud-sql                       yes    yes
data-fusion                     yes    yes
dataprep                        yes    yes
dataplex                        yes    yes
data-catalog                    yes    yes
looker-studio                   yes    yes
sensitive-data-protection       yes    yes

A 'NO' in the EU column means the workload cannot be run entirely
inside the EU with that service. That is a design constraint, not
a paperwork problem: the compute has to live somewhere.
```

### Lab 2 — The residency map of the course pipeline

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import get_service

# Every resource in the course pipeline, and where it must live for the
# data to stay in one geography.
PIPELINE_RESOURCES = [
    ("raw events", "cloud-storage", "gs://raw/events/"),
    ("staging", "cloud-storage", "gs://staging/events/"),
    ("quarantine (dead letter)", "cloud-storage", "gs://quarantine/events/"),
    ("warehouse table", "bigquery", "analytics.events"),
    ("summary table", "bigquery", "analytics.events_summary"),
    ("stream bus", "pubsub", "events-normalised"),
    ("batch engine", "dataproc", "ephemeral Spark cluster"),
    ("orchestrator", "composer", "Composer environment"),
    ("transformation", "dataform", "repository + workspace"),
    ("catalog", "data-catalog", "entry groups + tags"),
    ("governance", "dataplex", "lake + zone"),
    ("PII redaction", "sensitive-data-protection", "inspect + de-identify"),
    ("BI", "looker-studio", "report + data source"),
]

TARGET = "europe-west4"

print(f"Residency map — everything must resolve to {TARGET}")
print(f"{'pipeline stage':<28} {'service':<28} {'resource':<34} {'region':>14}")
print("-" * 110)
for stage, service_id, resource in PIPELINE_RESOURCES:
    service = get_service(service_id)
    print(f"{stage:<28} {service.name:<28} {resource:<34} {TARGET:>14}")
print()
print("Note what is NOT in this list: nothing. Every stage has a region.")
print("A residency breach is always one of these resources sitting in")
print("the wrong place — usually the compute, because the compute is")
print("where the engineers put it by default.")
```

Expected output:

```text
Residency map — everything must resolve to europe-west4
pipeline stage               service                      resource                                   region
--------------------------------------------------------------------------------------------------------------
raw events                   Cloud Storage                gs://raw/events/                     europe-west4
staging                      Cloud Storage                gs://staging/events/                 europe-west4
quarantine (dead letter)     Cloud Storage                gs://quarantine/events/              europe-west4
warehouse table              BigQuery                     analytics.events                     europe-west4
summary table                BigQuery                     analytics.events_summary             europe-west4
stream bus                   Pub/Sub                      events-normalised                    europe-west4
batch engine                 Dataproc                     ephemeral Spark cluster              europe-west4
orchestrator                 Cloud Composer               Composer environment                 europe-west4
transformation               Dataform                     repository + workspace               europe-west4
catalog                      Data Catalog                 entry groups + tags                  europe-west4
governance                   Dataplex                     lake + zone                          europe-west4
PII redaction                Sensitive Data Protection    inspect + de-identify                europe-west4
BI                           Looker Studio                report + data source                 europe-west4

Note what is NOT in this list: nothing. Every stage has a region.
A residency breach is always one of these resources sitting in
the wrong place — usually the compute, because the compute is
where the engineers put it by default.
```

### Lab 3 — Model the CMEK key hierarchy

```python
from dataclasses import dataclass, field


@dataclass
class KeyVersion:
    number: int
    state: str
    algorithm: str = "GOOGLE_SYMMETRIC_ENCRYPTION"

    @property
    def usable(self) -> bool:
        return self.state == "ENABLED"


@dataclass
class CryptoKey:
    name: str
    location: str            # the key RING's location
    purpose: str = "ENCRYPT_DECRYPT"
    versions: list[KeyVersion] = field(default_factory=list)
    # Who holds what. This is the part that actually matters.
    encrypter_members: list[str] = field(default_factory=list)
    encrypter_decrypter_members: list[str] = field(default_factory=list)

    def add_version(self, number: int) -> None:
        self.versions.append(KeyVersion(number, "ENABLED"))

    def disable(self, number: int) -> None:
        for version in self.versions:
            if version.number == number:
                version.state = "DISABLED"

    def active_versions(self) -> list[KeyVersion]:
        return [v for v in self.versions if v.usable]


# The key for the analytics warehouse.
bq_key = CryptoKey(
    name="bigquery-events-key",
    location="europe-west4",
)
bq_key.add_version(1)

# The service account that WRITES the data needs only encrypter.
bq_key.encrypter_members.append("bq-writer@my-project.iam.gserviceaccount.com")
# The data team reads through BigQuery, so they need no key access at all.
bq_key.encrypter_decrypter_members.append("bigquery-service-agent@my-project.iam.gserviceaccount.com")

print("Key hierarchy")
print(f"  organization")
print(f"    └── project: my-project")
print(f"          └── key ring: my-project/europe-west4")
print(f"                └── crypto key: {bq_key.name}")
print(f"                      purpose: {bq_key.purpose}")
print(f"                      location: {bq_key.location}")
for version in bq_key.versions:
    print(f"                      └── version {version.number}: {version.state}")
print()

print("IAM on the key")
print(f"  cloudkms.cryptoKeyEncrypter")
for member in bq_key.encrypter_members:
    print(f"      {member}")
print(f"  cloudkms.cryptoKeyEncrypterDecrypter")
for member in bq_key.encrypter_decrypter_members:
    print(f"      {member}")
print()

# The audit that matters: does a HUMAN hold decrypt?
humans = [m for m in bq_key.encrypter_decrypter_members if not m.endswith(".gserviceaccount.com")]
print(f"human identities with decrypt access: {len(humans)}")
if humans:
    for member in humans:
        print(f"  [FAIL] {member}")
    print("  A human who can decrypt the key can decrypt every table")
    print("  protected by it, regardless of their BigQuery IAM.")
else:
    print("  [PASS] no human holds decrypt on the key")
print()
print("Humans read through the service, not through the key.")
print("Grant BigQuery read on the table; do NOT grant KMS decrypt.")
print()

# Rotation.
print("Key rotation")
print(f"  active versions before rotation: {[v.number for v in bq_key.active_versions()]}")
bq_key.add_version(2)
print(f"  after creating version 2:        {[v.number for v in bq_key.active_versions()]}")
bq_key.disable(1)
print(f"  after disabling version 1:        {[v.number for v in bq_key.active_versions()]}")
print("  Data written with v1 stays readable until v1 is DESTROYED.")
```

Expected output:

```text
Key hierarchy
  organization
    └── project: my-project
          └── key ring: my-project/europe-west4
                └── crypto key: bigquery-events-key
                      purpose: ENCRYPT_DECRYPT
                      location: europe-west4
                      └── version 1: ENABLED

IAM on the key
  cloudkms.cryptoKeyEncrypter
      bq-writer@my-project.iam.gserviceaccount.com
  cloudkms.cryptoKeyEncrypterDecrypter
      bigquery-service-agent@my-project.iam.gserviceaccount.com

human identities with decrypt access: 0
  [PASS] no human holds decrypt on the key

Humans read through the service, not through the key.
Grant BigQuery read on the table; do NOT grant KMS decrypt.

Key rotation
  active versions before rotation: [1]
  after creating version 2:        [1, 2]
  after disabling version 1:        [2]
  Data written with v1 stays readable until v1 is DESTROYED.
```

### Lab 4 — CMEK as a residency enforcement mechanism

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class KeyRing:
    name: str
    location: str


@dataclass(frozen=True)
class Resource:
    name: str
    location: str
    key_ring: KeyRing | None = None


def can_use_key(resource: Resource, key_ring: KeyRing) -> bool:
    """A key ring only protects resources in the same location."""
    if resource.key_ring is None:
        return True   # no CMEK, no constraint
    return resource.key_ring.location == key_ring.location


def residency_ok(resource: Resource, allowed: set[str]) -> bool:
    return resource.location in allowed


EU = {"europe-west1", "europe-west2", "europe-west4"}

# An EU key ring.
eu_ring = KeyRing("my-project/eu-keyring", "europe-west4")

# A dataset in the EU, protected by the EU key.
eu_dataset = Resource("analytics.events", "europe-west4", eu_ring)

# A dataset in the US, trying to use the EU key.
us_dataset = Resource("analytics.events_us", "us-central1", eu_ring)

# A dataset in the EU with a US key.
misplaced_dataset = Resource("analytics.events_misplaced", "europe-west4",
                             KeyRing("my-project/us-keyring", "us-central1"))

# A dataset with no CMEK at all.
unprotected = Resource("analytics.events_plain", "europe-west4", None)

print(f"{'resource':<28} {'location':<14} {'key ring location':<20} {'CMEK ok':>8} {'residency':>11}")
print("-" * 84)
for resource in (eu_dataset, us_dataset, misplaced_dataset, unprotected):
    ring_loc = resource.key_ring.location if resource.key_ring else "-"
    print(f"{resource.name:<28} {resource.location:<14} {ring_loc:<20} "
          f"{str(can_use_key(resource, eu_ring)):>8} "
          f"{str(residency_ok(resource, EU)):>11}")
print()

print("CMEK is not a policy. A key ring in europe-west4 physically")
print("cannot protect a dataset in us-central1 — the API rejects it.")
print("That is why CMEK is the strongest residency control available:")
print("it makes the violation impossible rather than merely discouraged.")
print()
print("Note the 'residency' column: the unprotected EU dataset is")
print("residency-compliant but not key-controlled. The two checks are")
print("independent, and a regulated workload needs both.")
```

Expected output:

```text
resource                     location       key ring location     CMEK ok   residency
------------------------------------------------------------------------------------
analytics.events             europe-west4   europe-west4             True        True
analytics.events_us          us-central1    europe-west4             True       False
analytics.events_misplaced   europe-west4   us-central1             False        True
analytics.events_plain       europe-west4   -                        True        True

CMEK is not a policy. A key ring in europe-west4 physically
cannot protect a dataset in us-central1 — the API rejects it.
That is why CMEK is the strongest residency control available:
it makes the violation impossible rather than merely discouraged.

Note the 'residency' column: the unprotected EU dataset is
residency-compliant but not key-controlled. The two checks are
independent, and a regulated workload needs both.
```

### Lab 5 — Model the shared responsibility over the pipeline

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts, redact_pii

LAYERS = [
    ("Physical infrastructure", "Google", "You", "data centre, power, cooling, server hardware"),
    ("Virtualisation / hypervisor", "Google", "You", "host isolation, hypervisor patches"),
    ("Storage encryption at rest", "Google (managed keys)", "You (with CMEK)", "key custody, rotation, revocation"),
    ("Network encryption", "Google", "You", "TLS config, private IP, VPC-SC perimeter"),
    ("Identity & access", "Google (IAM engine)", "You", "who gets which role, and when it is removed"),
    ("Audit logging", "Google (produces)", "You (triage)", "alerting, investigation, evidence retention"),
    ("Data classification", "You", "You", "tags, sensitivity levels, retention labels"),
    ("Data minimisation", "You", "You", "which columns are copied downstream"),
    ("Deletion on request", "You", "You", "a working path from every copy, including quarantine"),
    ("Application code", "You", "You", "no PII in logs, no raw payloads in errors"),
    ("Residency of compute", "You", "You", "every job that touches the data runs in-region"),
]

print(f"{'layer':<32} {'Google':<22} {'You':<22} {'what it means'}")
print("-" * 112)
for layer, google, you, note in LAYERS:
    print(f"{layer:<32} {google:<22} {you:<22} {note}")
print()

# The layer that bites: the quarantine path.
bad = ingest_events(open("sample_data/malformed_events.csv").read().splitlines())[1]
print("The quarantine path — the copy nobody thinks about")
print(f"  rejected rows written to a dead-letter store: {len(bad)}")
print()
print("Each rejected row carries a raw payload. That store is:")
print("  - a second copy of the data, with the same PII in it")
print("  - NOT covered by the pipeline's de-identification")
print("  - NOT covered by a retention rule unless you write one")
print()

# Show what a leaked log line would look like.
sample_raw = bad[0]["raw"] if bad else ""
print("A raw rejected row looks like this in a log:")
print(f"  {sample_raw[:80]!r}")
print()
print("If that row contains an email, the log now contains an email.")
print("The 'no PII in logs' rule is a code rule, and it is yours.")
```

Expected output:

```text
layer                            Google                 You                    what it means
----------------------------------------------------------------------------------------------------------------
Physical infrastructure          Google                 You                    data centre, power, cooling, server hardware
Virtualisation / hypervisor      Google                 You                    host isolation, hypervisor patches
Storage encryption at rest       Google (managed keys)  You (with CMEK)        key custody, rotation, revocation
Network encryption               Google                 You                    TLS config, private IP, VPC-SC perimeter
Identity & access                Google (IAM engine)    You                    who gets which role, and when it is removed
Audit logging                    Google (produces)      You (triage)           alerting, investigation, evidence retention
Data classification              You                    You                    tags, sensitivity levels, retention labels
Data minimisation                You                    You                    which columns are copied downstream
Deletion on request              You                    You                    a working path from every copy, including quarantine
Application code                 You                    You                    no PII in logs, no raw payloads in errors
Residency of compute             You                    You                    every job that touches the data runs in-region

The quarantine path — the copy nobody thinks about
  rejected rows written to a dead-letter store: 12

Each rejected row carries a raw payload. That store is:
  - a second copy of the data, with the same PII in it
  - NOT covered by the pipeline's de-identification
  - NOT covered by a retention rule unless you write one

A raw rejected row looks like this in a log:
  'e00004799,u000002,2026-01-15T23:59:00Z,signup,EMEA,web,EUR,10.0'

If that row contains an email, the log now contains an email.
The 'no PII in logs' rule is a code rule, and it is yours.
```

### Lab 6 — Test the deletion path

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, redact_pii, looks_like_email

# Deletion is the hardest regulatory capability to get right, because
# the data lives in many places. Here is the inventory.
COPIES = [
    ("BigQuery raw table", "analytics.events", "partition delete + MERGE"),
    ("BigQuery summary table", "analytics.events_summary", "aggregate rebuild"),
    ("Cloud Storage landing zone", "gs://raw/events/", "object delete + lifecycle"),
    ("Cloud Storage quarantine", "gs://quarantine/events/", "object delete + lifecycle"),
    ("Pub/Sub message backlog", "events-normalised", "ack + retention policy"),
    ("BigQuery audit logs", "cloudaudit.googleapis.com", "log sink retention"),
    ("Looker Studio cached data", "report data source", "cache TTL + source fix"),
    ("DLP findings report", "gs://dlp-reports/", "object delete + lifecycle"),
]

print("Deletion inventory — every copy must be listed")
print(f"{'copy':<32} {'location':<34} {'mechanism'}")
print("-" * 100)
for copy_name, location, mechanism in COPIES:
    print(f"{copy_name:<32} {location:<34} {mechanism}")
print()
print(f"total copies to handle: {len(COPIES)}")
print()

# Demonstrate the redaction that must happen BEFORE the data lands
# in any of those copies.
records = [
    "Contact alice@example.com about order 12345",
    "Call 555-123-4567 or write bob@example.org",
    "Order 12346 has no contact details",
]

print("Redaction applied before any copy is made")
for record in records:
    cleaned = record
    for token in cleaned.split():
        if looks_like_email(token):
            cleaned = cleaned.replace(token, redact_pii(token, keep_last=4))
    print(f"  in : {record}")
    print(f"  out: {cleaned}")
    print()
```

Expected output:

```text
Deletion inventory — every copy must be listed
copy                             location                           mechanism
----------------------------------------------------------------------------------------------------
BigQuery raw table               analytics.events                   partition delete + MERGE
BigQuery summary table           analytics.events_summary           aggregate rebuild
Cloud Storage landing zone       gs://raw/events/                   object delete + lifecycle
Cloud Storage quarantine         gs://quarantine/events/            object delete + lifecycle
Pub/Sub message backlog          events-normalised                  ack + retention policy
BigQuery audit logs              cloudaudit.googleapis.com          log sink retention
Looker Studio cached data        report data source                 cache TTL + source fix
DLP findings report              gs://dlp-reports/                  object delete + lifecycle

total copies to handle: 8

Redaction applied before any copy is made
  in : Contact alice@example.com about order 12345
  out: Contact *************.com about order 12345

  in : Call 555-123-4567 or write bob@example.org
  out: Call 555-123-4567 or write ***********.org

  in : Order 12346 has no contact details
  out: Order 12346 has no contact details
```

### Lab 7 — The compliance claim checklist

```python
from dataclasses import dataclass


@dataclass
class Claim:
    statement: str
    backed_by: str
    google_provides: bool
    you_provide: bool


CLAIMS = [
    Claim("Our data is encrypted at rest",
          "Google-managed keys, or CMEK",
          True, True),
    Claim("Our data stays in the EU",
          "Regional placement + CMEK key ring location + VPC-SC",
          False, True),
    Claim("Only two engineers can read the customer table",
          "IAM + VPC-SC perimeter + CMEK key IAM",
          False, True),
    Claim("We can delete a customer's data on request",
          "A tested deletion path across every copy",
          False, True),
    Claim("We do not log personal data",
          "Application code + log sinks",
          False, True),
    Claim("Google is HIPAA compliant",
          "Google's BAA + eligible services only",
          True, True),
    Claim("Our platform is SOC 2 audited",
          "Google's SOC 2 report covers GOOGLE, not you",
          True, False),
    Claim("We are FedRAMP authorised",
          "Only for federal workloads in authorised regions",
          False, True),
]

print(f"{'claim':<44} {'Google':>8} {'you':>6} {'verdict'}")
print("-" * 92)
for claim in CLAIMS:
    if claim.google_provides and claim.you_provide:
        verdict = "jointly supported"
    elif claim.google_provides:
        verdict = "Google's claim only"
    else:
        verdict = "YOUR obligation"
    print(f"{claim.statement:<44} {str(claim.google_provides):>8} "
          f"{str(claim.you_provide):>6}   {verdict}")
print()
print("The pattern: every compliance claim that touches YOUR data is")
print("YOUR obligation, regardless of what Google certifies.")
```

Expected output:

```text
claim                                          Google    you verdict
--------------------------------------------------------------------------------------------
Our data is encrypted at rest                    True   True   jointly supported
Our data stays in the EU                        False   True   YOUR obligation
Only two engineers can read the customer table    False   True   YOUR obligation
We can delete a customer's data on request      False   True   YOUR obligation
We do not log personal data                     False   True   YOUR obligation
Google is HIPAA compliant                        True   True   jointly supported
Our platform is SOC 2 audited                    True  False   Google's claim only
We are FedRAMP authorised                       False   True   YOUR obligation

The pattern: every compliance claim that touches YOUR data is
YOUR obligation, regardless of what Google certifies.
```

---

## 🛠️ Common Errors and Fixes

### 1. `400 Bad Request` — the Cloud KMS key ring location does not match the resource

```text
INVALID_ARGUMENT: The provided encryption key is invalid. Key
projects/my-project/locations/europe-west4/keyRings/eu-keyring/cryptoKeys/bq-key
cannot be used to encrypt a BigTable in location us-central1.
```

**Cause:** the CMEK key ring's location must match the resource's location. This is the mechanism that enforces residency with CMEK, and it is also the most common CMEK setup error.

**Fix:** create a key ring in the same region as the resource and re-apply the key.

```bash
gcloud kms keyrings create eu-keyring \
  --location=europe-west4 --project=my-project

gcloud kms keys create bq-key \
  --location=europe-west4 --keyring=eu-keyring \
  --purpose=encryption --project=my-project
```

### 2. `403 Permission denied` — the service account lacks the KMS permission

```text
PERMISSION_DENIED: Permission 'cloudkms.cryptoKeyEncrypter' denied on
resource 'projects/my-project/locations/europe-west4/keyRings/eu-keyring/cryptoKeys/bq-key'.
```

**Cause:** the identity writing to the encrypted resource has no `cloudkms.cryptoKeyEncrypter` on the key. For BigQuery with CMEK, the **BigQuery service agent** for the project needs the permission, not your pipeline's service account.

**Fix:** grant the BigQuery service agent the encrypter role on the key.

```bash
gcloud kms keys add-iam-policy-binding bq-key \
  --location=europe-west4 --keyring=eu-keyring --project=my-project \
  --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-bigquery-encryption.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypter
```

### 3. `403 Permission denied` on `cloudkms.cryptoKeyVersions.useToEncrypt`

```text
PERMISSION_DENIED: Permission 'cloudkms.cryptoKeyVersions.useToEncrypt'
denied on resource 'projects/my-project/locations/europe-west4/keyRings/eu-keyring/cryptoKeys/bq-key/cryptoKeyVersions/1'.
```

**Cause:** the key version is in the wrong state. A version that is `DISABLED`, `PENDING_DESTROY`, or `DESTROYED` cannot be used.

**Fix:** enable a version, and check the version's state before assuming an IAM problem.

```bash
gcloud kms keys versions list \
  --location=europe-west4 --keyring=eu-keyring --key=bq-key --project=my-project

gcloud kms keys versions enable 2 \
  --location=europe-west4 --keyring=eu-keyring --key=bq-key --project=my-project
```

### 4. `400 Bad Request` — `cmekSettings` names a key that does not exist

```text
INVALID_ARGUMENT: The KMS key version projects/my-project/locations/
us-central1/keyRings/kr/cryptoKeys/my-key/cryptoKeyVersions/3 does not
exist or is not enabled.
```

**Cause:** the `cmekSettings.kmsKeyName` must point at a **specific CryptoKeyVersion** (ending in `/cryptoKeyVersions/N`), not at the key itself. Pointing at the key gives an error; pointing at a version that was destroyed also gives this error.

**Fix:** reference the version explicitly.

```bash
gcloud kms keys versions list \
  --location=us-central1 --keyring=kr --key=my-key --project=my-project \
  --filter="state=ENABLED" --format="value(name)"
```

### 5. `PERMISSION_DENIED` — a VPC-SC perimeter blocks an internal service

```text
ERROR: HTTPError 403: The caller does not have permission
accesses.googleapis.com. The request is denied by the service
perimeter 'projects/123456789/locations/global/servicePerimeters/regulated'.
```

**Cause:** a VPC Service Controls perimeter is denying an access that is legitimate. The usual causes are: the calling service's service agent is not in the perimeter's allowed list; the access level is `ALLOW` but the caller is in a different perimeter; or an API is not in the perimeter's list of protected resources and the default is deny.

**Fix:** add the calling principal to the perimeter's access rules, and make sure the perimeter includes the services you actually need.

```bash
gcloud access-approval policies list \
  --project=my-project --location=global

gcloud beta services perimeters update regulated \
  --project=my-project --location=global \
  --add-access-rule="accessLevel=ALLOW,\
members=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-dataproc.iam.gserviceaccount.com"
```

### 6. Cloud SQL: `SSL connection is required` / `Access denied for user`

```text
ERROR 2024/03/15 10:22:01: [Note] [MYSQL] [Warning] SSL connection is
required without client's private key. The server might have switched
to a less secure mode.
```

**Cause:** the Cloud SQL instance has `require_ssl` enabled (or the MySQL `sslMode` is `ENCRYPTED_ONLY`) and the client is connecting without TLS — typically because a `sslMode=DISABLED` or `sslmode=disable` was set somewhere in the connection string.

**Fix:** use TLS on the client side and, for MySQL, prefer `TRUSTED_CLIENT_CERTIFICATE` with a client certificate so that the identity is cryptographically verified rather than just encrypted.

```bash
gcloud sql instances patch my-instance \
  --ssl-mode=TRUSTED_CLIENT_CERTIFICATE --require-ssl

gcloud sql users create reporting \
  --instance=my-instance --type=REQUIRED --password-file=/dev/stdin
```

### 7. A BigQuery dataset created in the wrong location, and the data cannot be moved

```text
ERROR: 400 Bad Request: Cannot change the location of dataset
my-project:analytics. Location is immutable.
```

**Cause:** a BigQuery dataset's location is **immutable**. Copying the data to a new dataset in the right region is the only way to move it.

**Fix:** create the destination dataset in the correct region, copy the tables, verify the row counts, and then switch the consumers over. Do this *before* you need it — a residency breach discovered during an audit is much worse than a proactive move.

```bash
bq mk --location=europe-west4 my-project:analytics_eu

bq cp my-project:analytics.events my-project:analytics_eu.events \
  --project_id=my-project
```

### 8. The service account for the pipeline can decrypt the key, and that defeats the purpose

**Cause:** not an error — a finding. Someone granted `roles/cloudkms.cryptoKeyEncrypterDecrypter` to a pipeline service account "so it can work", and now that service account can decrypt every resource protected by the key. If it is compromised, the attacker reads plaintext directly from Cloud KMS, bypassing the BigQuery IAM entirely.

**Fix:** the service only needs `cloudkms.cryptoKeyEncrypter`. Decryption happens inside the service using its own service agent, which is a Google-managed identity you cannot impersonate.

```bash
# Remove the decrypt role from the pipeline's service account
gcloud kms keys remove-iam-policy-binding bq-key \
  --location=europe-west4 --keyring=eu-keyring --project=my-project \
  --member=serviceAccount:pipeline@my-project.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter
```

---

## 💡 Production Notes

- **Choose the region before you create anything.** BigQuery dataset locations and Cloud KMS key ring locations are immutable. "We will move it later" is not a plan — it is a quarter of copying and a window of non-compliance.

- **Verify the region of the *compute*, not just the storage.** The residency breach in practice is a Composer environment, a Dataproc cluster, or a Data Fusion instance left in the company's default region. Audit every job that reads the data.

- **Never give a human `cloudkms.cryptoKeyEncrypterDecrypter`.** Humans read through the service. Grant BigQuery read on the table; the service's service agent does the decryption. A human with decrypt on the key bypasses every other access control you have.

- **Treat the key's IAM as your most sensitive access list.** It is the one place where possession means plaintext, regardless of what the data-plane IAM says. Audit it on the same cadence as your IAM, and alert on changes to it.

- **CMEK enforces residency technically, not just by policy.** A key ring in `europe-west4` physically cannot protect a `us-central1` resource. That is why CMEK is the strongest residency control available — prefer it over documentation.

- **Schedule key rotation and verify it happens.** Create the new version, switch the resource to it, then disable the old one. A rotation that is never verified is a rotation that did not happen.

- **Export Cloud Audit Logs to a sink the data owners cannot delete from.** In-project logs are logs the project owner can alter — which means they are not evidence. A bucket in a separate, tightly-controlled project (or a log bucket with retention locked) is the standard.

- **VPC Service Controls is the control that stops credential exfiltration.** CMEK tells you who holds the key; VPC-SC tells you from where data can be read. A stolen service account is blocked by the perimeter even if it has full data-plane IAM.

- **Inventory every copy of the data before claiming you can delete it.** The quarantine bucket, the landing zone, the Pub/Sub backlog, the DLP findings report, the Looker Studio cache, the audit logs. The course pipeline's dead-letter path is a real second copy of the raw rows, and it is the one nobody remembers.

- **Never log raw payloads.** The pipeline's rejected rows carry a `raw` field. Log the reason code and a truncated identifier, never the payload. `reject_counts` is designed to be the alertable metric precisely because it is safe.

- **Apply a lifecycle rule to the quarantine path on day one.** It accumulates fast, it holds the least-protected copy of the data, and a retention rule is the cheapest control available.

- **Keep the records of processing activities (GDPR Article 30) and the data inventory (MAS classification) in the data catalog as tags.** They are the same artefact with different names. Tag templates exist for exactly this, and an auditor will ask for the inventory, not the architecture diagram.

- **Do not inherit a compliance claim from a vendor.** "We are on GCP so we are compliant" is the wrong sentence. "We are on GCP, we have signed the BAA, we use only eligible services, our access is reviewed quarterly, and we can produce evidence for each of these" is the right one.

---

## 🔑 Key Takeaways

- **Residency is three questions**, not one: where is the data stored, where is it processed, and where are the backups. Placing storage correctly while computing elsewhere is a breach.
- **Multi-regional and dual-regional are availability choices, not residency ones.** The `EU` multi-region satisfies an EU requirement; `US` never does.
- **GDPR is not primarily a data-residency law.** It mandates a lawful basis, minimisation, security, and rights — and its real engineering consequences are deletion, minimisation, and auditability.
- **Singapore's PDPA** adds consent, purpose limitation, protection, retention limitation, and breach notification; **MAS TRM** adds data classification, CMEK, access reviews, and cloud-vendor risk assessment for financial institutions.
- **Google's certifications cover Google, not you.** SOC 2, ISO, PCI DSS Level 1, HIPAA eligibility, and FedRAMP are all statements about Google's controls and infrastructure. Every claim about *your* data is your obligation.
- **The shared responsibility split:** Google owns the infrastructure, the hypervisor, the base platform, and the managed-key rotation. You own your data, your configuration, your code, your identities, your key custody, and your evidence.
- **CMEK moves trust from the data plane to the key plane.** Your data is unreadable without your key; your key's IAM is your access-control model.
- **A key ring's location must match the resource's location**, which makes CMEK a *technical* residency control rather than a policy one.
- **Never give a human `cryptoKeyEncrypterDecrypter`.** The service needs `cryptoKeyEncrypter`; the service's service agent handles decryption. A human with decrypt bypasses every data-plane control.
- **TLS is everywhere and not optional.** What you configure is the client side — Cloud SQL `require_ssl`, `sslMode=ENCRYPTED_ONLY` or `TRUSTED_CLIENT_CERTIFICATE`, and the Cloud SQL Auth Proxy.
- **VPC-SC is the perimeter control.** It stops a stolen credential from exfiltrating data outside the perimeter — the scenario CMEK alone does not solve.
- **Deletion is the hardest capability to build**, because the data lives in many copies. Inventory them all, including the dead-letter quarantine and the audit logs.
- **Minimisation is both the compliant design and the cheap one.** The `region_reference.ndjson` lookup table is the pattern: reference, don't copy.

---

## 📚 Practice Exercises

1. **Residency map.** For the course pipeline, produce a complete resource inventory: every bucket, dataset, topic, cluster, environment, repository, catalog entry, and BI report. For each, record its region and whether it is inside the EU, and identify the three resources most likely to be in the wrong place. Use `service_catalog.get_service` and `regions_for` to verify that each service is available in the target region.

2. **CMEK key design.** Design the full key hierarchy for the pipeline: key rings per region, keys per resource class, and the IAM on each. State precisely who holds `cryptoKeyEncrypter`, who holds `cryptoKeyEncrypterDecrypter`, and why the second list contains only Google-managed service agents. Then write the `audit_key_iam` function that asserts no human identity holds decrypt.

3. **Rotation drill.** Write a rotation runbook: create version N+1, migrate the resource to it, verify the data is readable, disable version N, and schedule the destroy of version N after the retention window. Include the check that catches a resource that was silently not migrated — and explain why disabling a version before migrating makes data permanently unreadable.

4. **Shared responsibility audit.** Take the course pipeline layer by layer and, for each, write the specific GCP artefact that evidences your compliance: the IAM binding, the log sink, the lifecycle rule, the tag, the key version, the test result. Then identify the three layers where your evidence is currently weakest.

5. **Deletion rehearsal.** Using `ingest_events` and the reject path from `project/core/pipeline_logic.py`, simulate a deletion request for one `user_id`. Trace the record through every copy in the Lab 6 inventory: the raw table, the summary, the landing zone, the quarantine, the Pub/Sub backlog, the logs, and the BI cache. Write down what each step would do — and mark every step you cannot actually perform.

6. **Compliance claim review.** Take five claims from a real marketing page or contract (or invent five plausible ones). For each, apply the Lab 7 framework: what does Google provide, what must you provide, and is the claim accurate as written? Rewrite any overreaching claim into one that is defensible, and list the evidence you would need to keep it.

7. **MAS TRM mapping.** Map each MAS TRM expectation (data classification, encryption with customer-held keys, access control, access review, audit logging, cloud third-party risk management) to a specific GCP mechanism. For each, state the artefact that proves compliance, and the cadence at which you would produce it.

8. **Residency breach exercise.** Assume a Composer environment in `us-central1` reads a BigQuery dataset in `europe-west4` and writes the results back. Trace the three residency questions (stored, processed, backed up) and state precisely what has happened. Then design the fix, including the migration of the Composer environment and the Composer DAGs, and estimate the blast radius of the change.

---

## 📖 Further Reading

- [Google Cloud Compliance and Certifications](https://cloud.google.com/security/compliance)
- [Google Cloud Shared Responsibility Model](https://cloud.google.com/security/compliance/shared-responsibility)
- [Data Residency Controls in Google Cloud](https://cloud.google.com/security/compliance/data-residency-controls)
- [Cloud KMS Documentation](https://docs.cloud.google.com/kms/docs)
- [Creating and Managing Encryption Keys](https://docs.cloud.google.com/kms/docs/create-key-versions)
- [VPC Service Controls Documentation](https://docs.cloud.google.com/vpc-service-controls/docs)
- [Google Cloud Compliance offerings — HIPAA and PCI DSS](https://cloud.google.com/security/compliance/hipaa)
