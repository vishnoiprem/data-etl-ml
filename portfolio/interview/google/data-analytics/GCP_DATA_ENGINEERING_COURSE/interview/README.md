# GCP Data Engineering — Interview Question Bank

A certification-style and interview-style question bank for the Google Cloud
Data Engineer course. **128 questions** across seven files, every one written
the way a senior engineer answers in an interview: a direct answer in the first
sentence, then the mechanism, then the trade-off, then a concrete production
detail or number — and, where it earns its place, a failure story.

---

## 🎯 How to use this bank

This bank is a **mirror**, not a textbook. The chapters in `../chapters/` teach
the material; this bank trains you to *say it under pressure*. Reading a chapter
and reading an answer are different skills — one is comprehension, the other is
recall under time pressure with an interviewer watching.

Work through it like this:

1. **Read the question and answer it out loud**, before you read the model's
   answer. Out loud, because silent reading lets you recognise a good answer
   without being able to produce one.
2. **Read the answer's first sentence.** That is the sentence that has to come
   out of your mouth first. If you cannot reproduce it from memory, you do not
   know the question yet.
3. **Read the mechanism.** This is where the question turns from recall into
   reasoning — and it is what lets you adapt the answer to a question that is
   phrased differently than you expected.
4. **Run the code.** Every "Check yourself" block is real, runnable Python
   against the course's own modules. It exercises the same invariant the
   question is about.
5. **Come back the next day** and answer again from memory. The second attempt
   is the one that counts.

The bank is ordered by *topic*, not by difficulty, and the topic files follow
the course's module structure. If you are preparing for the certification,
work the files in order — the exam's domains follow the same shape. If you are
preparing for an interview, work [`top-40.md`](top-40.md) twice and use the
topic files as reference.

---

## 📁 The files

| File | Questions | Covers | Modules |
|---|---:|---|---|
| [`01-platform-fundamentals.md`](01-platform-fundamentals.md) | 14 | Cloud concepts, regions and zones, resource hierarchy, IAM, service accounts, org policies, networking, compute | 1 |
| [`02-storage-and-databases.md`](02-storage-and-databases.md) | 14 | Cloud Storage, block and file storage, Cloud SQL, Spanner, Bigtable, Datastore/Firestore, Memorystore, database selection | 2 |
| [`03-analytics-and-cost.md`](03-analytics-and-cost.md) | 16 | BigQuery, partitioning, clustering, schemas, optimisation, BigLake, Dataplex, Data Catalog, cost modelling | 3 |
| [`04-streaming-and-ingestion.md`](04-streaming-and-ingestion.md) | 14 | Kafka, Pub/Sub, Datastream and CDC, transfer services, delivery semantics | 4 |
| [`05-processing-and-orchestration.md`](05-processing-and-orchestration.md) | 16 | Hadoop, Spark/Dataproc, Beam/Dataflow, Airflow/Composer/Workflows, Dataform, Data Fusion, Dataprep | 5, 6 |
| [`06-governance-security-and-ml.md`](06-governance-security-and-ml.md) | 14 | DLP, residency, compliance, encryption, CMEK, Looker Studio and BI, ML fundamentals, Vertex AI, BigQuery ML | 7, 8 |
| [`top-40.md`](top-40.md) | 40 | The highest-yield questions, consolidated, for a final cramming pass | all |
| **Total** | **128** | | |

Every question has the same anatomy:

- **Answer** — the direct first sentence.
- **Mechanism** — *why* the platform behaves that way.
- **Trade-off** — what the choice costs, and when the other option wins.
- **In practice** — a concrete number, a role, or a configuration.
- **Failure story** — where it goes wrong in production (where it earns its place).
- **Check yourself** — runnable Python against `project/core/`.

---

## 📅 The 14-day schedule

Fourteen days, roughly two hours a day. Each day has a **learn** block
(read the linked chapters), a **drill** block (answer questions out loud), and a
**lab** block (run the code and compare against the verified outputs).

### Days 1–3 — Platform fundamentals

| Day | Learn | Drill | Lab |
|---|---|---|---|
| **1** | `chapters/01`, `chapters/02` | `01` Q1–Q5 | `python project/local_runner.py --services` and `--regions` |
| **2** | `chapters/03`, `chapters/04` | `01` Q6–Q11 | `python project/local_runner.py --iam` |
| **3** | `chapters/05` | `01` Q12–Q14, then all 14 again from memory | `python project/local_runner.py --run` |

*Checkpoint: you can explain IAM inheritance and the blast-radius question
without notes, and you can read the demo IAM policy and say what each identity
may do.*

### Days 4–6 — Storage and databases

| Day | Learn | Drill | Lab |
|---|---|---|---|
| **4** | `chapters/06`, `chapters/07` | `02` Q1–Q7 | Work out the storage-class break-even for 40 TB read quarterly |
| **5** | `chapters/08`, `chapters/09`, `chapters/10` | `02` Q8–Q14 | `service_catalog.services_by_category("Databases")` and compare pricing models |
| **6** | `chapters/11` | All 14 of `02` again | Write your own database-selection decision table |

*Checkpoint: you can pick a database for a new requirement in under two
minutes, and justify it on access pattern, consistency and scale.*

### Days 7–9 — Analytics and cost

| Day | Learn | Drill | Lab |
|---|---|---|---|
| **7** | `chapters/12`, `chapters/13` | `03` Q1–Q8 | `python project/local_runner.py --cost` |
| **8** | `chapters/14` | `03` Q9–Q16 | `python project/local_runner.py --compare` |
| **9** | `chapters/15` | All 16 of `03` again | Compute the cost of a 10 TB unpartitioned `COUNT(*)` — then the partitioned version |

*Checkpoint: you can look at a slow or expensive query and name the four things
you would check, in order.*

### Days 10–11 — Streaming and ingestion

| Day | Learn | Drill | Lab |
|---|---|---|---|
| **10** | `chapters/16`, `chapters/17` | `04` Q1–Q8 | `bucket_by_window` on the sample data — confirm 24 windows |
| **11** | `chapters/18`, `chapters/19` | `04` Q9–Q14 | The malformed sample file — confirm all ten reject reason codes |

*Checkpoint: you can state exactly what Pub/Sub guarantees, what it does not,
and what your sink must do about it.*

### Days 12–13 — Processing, orchestration, governance and ML

| Day | Learn | Drill | Lab |
|---|---|---|---|
| **12** | `chapters/20`–`chapters/24` | `05` Q1–Q16 | `platform_sim.build_demo_project()` and `run_pipeline` end to end |
| **13** | `chapters/25`–`chapters/34` | `06` Q1–Q14 | `redact_pii` and `looks_like_email` — see why regex is not DLP |

*Checkpoint: you can explain the shared responsibility boundary, and say what
CMEK buys you and what it costs.*

### Day 14 — Final cramming pass

| Block | Activity |
|---|---|
| **Morning (60 min)** | Work through `top-40.md` Q1–Q20 out loud, no notes. Mark every question you hesitated on. |
| **Midday (45 min)** | Work through `top-40.md` Q21–Q40 the same way. |
| **Afternoon (45 min)** | Re-answer only the marked ones. Then do one full mock: pick five questions at random from any file and answer them in four minutes each, standing up. |
| **Evening (15 min)** | Read the failure stories you did not remember. They are the part interviewers probe, because they are the part you can only have if you have actually operated the platform. |

*Checkpoint: you can answer any question in the bank in under four minutes,
with the mechanism, and with one concrete number.*

---

## 📊 Self-assessment rubric

Mark each question **R**, **P** or **N** — and be honest, because the rubric
only helps if the marks are accurate.

| Mark | Meaning | What it actually tells you |
|---|---|---|
| **R** — Ready | You answered the direct question, gave the mechanism, and reached a concrete number or configuration without notes. | You can hold this in a real interview. |
| **P** — Partial | You got the direction right but could not articulate the mechanism, or you had the trade-off but no production detail. | You recognised the answer but have not internalised it. Revisit the mechanism, not the conclusion. |
| **N** — Not yet | You guessed, or you had to read the answer. | This is a gap. Re-read the linked chapter before moving on. |

### The scoring bands

| Band | Every question | What it means |
|---|---|---|
| **Interview-ready** | 90%+ R, no N in the top 40 | You can defend your answers under follow-up. Expect to be asked "why not the alternative?" on every design question — the trade-off section is what answers that. |
| **Nearly there** | 75–89% R, remaining are mostly P | You know the material. Your weak spots are the production details and the numbers. Drill those specifically — they are the easiest to fix. |
| **Needs work** | 50–74% R | You have read but not absorbed. Repeat the 14-day schedule at half speed, one file per two days. |
| **Start the chapters** | Below 50% R | Read `../chapters/` in order first. This bank works as a mirror; it does not work as a substitute for the source material. |

### The follow-up test

A question marked **R** is not actually ready until you can also answer the
three follow-ups an interviewer will reach for:

1. **"What would break in production?"** — the failure story.
2. **"What would you do instead?"** — the trade-off, stated with a reason.
3. **"Can you give me a number?"** — the concrete figure.

If you can only do the first sentence, you have memorised a definition, not
mastered a topic. Those three follow-ups are where interviews are actually
won and lost.

---

## 🧰 The project modules behind the answers

Every "Check yourself" block runs against the course's own modules, which
import nothing from Google Cloud and need no account, credentials or bill:

| Module | What it gives the bank |
|---|---|
| [`project/core/service_catalog.py`](../project/core/service_catalog.py) | 34 services, 12 regions, 8 categories — the inventory every "which service is available where" answer draws on. |
| [`project/core/iam_policy.py`](../project/core/iam_policy.py) | 23 roles and a policy-evaluation engine with inheritance, conditions and explicit deny. |
| [`project/core/cost_model.py`](../project/core/cost_model.py) | Per-service pricing estimators and the architecture comparison behind the cost questions. |
| [`project/core/pipeline_logic.py`](../project/core/pipeline_logic.py) | The pure pipeline — validation, windowing, deduplication, redaction. |
| [`project/core/platform_sim.py`](../project/core/platform_sim.py) | A simulated project with a resource tree, an IAM policy and a runnable pipeline. |

Run the CLI from the course root:

```bash
python project/local_runner.py --list
python project/local_runner.py --services
python project/local_runner.py --regions
python project/local_runner.py --iam
python project/local_runner.py --run
python project/local_runner.py --cost
python project/local_runner.py --compare
```

The **verified outputs** you should be able to reproduce and explain — if your
numbers differ, one of them is wrong, and that is worth finding:

- 4800 events, 12 malformed rows, 50 reference rows, target date `2026-01-15`
- 24 hourly windows
- Summary CSV:

```text
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

- Reject counts:

```text
{'wrong_field_count': 2, 'bad_amount': 1, 'unknown_region': 2,
 'unknown_channel': 1, 'unknown_currency': 1, 'unknown_event_type': 1,
 'missing_event_id': 1, 'missing_user_id': 1, 'negative_amount': 1,
 'bad_timestamp': 1}
```

---

## 📚 Related chapters

Every question links back to its source chapter, and every chapter links here.
The full list:

- [1.1 — Introduction to Cloud Computing](../chapters/01-introduction-to-cloud-computing.md)
- [1.2 — Regions, Zones & the Resource Hierarchy](../chapters/02-regions-zones-and-resource-hierarchy.md)
- [1.3 — Identity & Access Management](../chapters/03-identity-and-access-management.md)
- [1.4 — Organization Policies, Networking & Compute](../chapters/04-org-policies-networking-and-compute.md)
- [1.5 — Proposing a Data Processing Strategy](../chapters/05-proposing-a-data-processing-strategy.md)
- [2.1 — Cloud Storage](../chapters/06-cloud-storage.md)
- [2.2 — Block & File Storage](../chapters/07-block-and-file-storage.md)
- [2.3 — Cloud SQL](../chapters/08-cloud-sql.md)
- [2.4 — Cloud Spanner](../chapters/09-cloud-spanner.md)
- [2.5 — NoSQL: Bigtable, Datastore, Firestore, Memorystore](../chapters/10-nosql-bigtable-datastore-firestore-memorystore.md)
- [2.6 — Selecting a Database](../chapters/11-selecting-a-database.md)
- [3.1 — Data Warehousing Concepts](../chapters/12-data-warehousing-concepts.md)
- [3.2 — BigQuery Platform Overview](../chapters/13-bigquery-platform-overview.md)
- [3.3 — BigQuery Query Optimization](../chapters/14-bigquery-query-optimization.md)
- [3.4 — BigLake, Dataplex & Data Catalog](../chapters/15-biglake-dataplex-and-data-catalog.md)
- [4.1 — Kafka & the Streaming Model](../chapters/16-kafka-and-the-streaming-model.md)
- [4.2 — Pub/Sub](../chapters/17-pubsub.md)
- [4.3 — Datastream & CDC](../chapters/18-datastream-and-cdc.md)
- [4.4 — Transfer Services & Migration](../chapters/19-transfer-services-and-migration.md)
- [5.1 — Hadoop & the Big Data Ecosystem](../chapters/20-hadoop-and-big-data-ecosystem.md)
- [5.2 — Apache Spark & Cloud Dataproc](../chapters/21-apache-spark-and-dataproc.md)
- [5.3 — Apache Beam & Cloud Dataflow](../chapters/22-apache-beam-and-dataflow.md)
- [5.4 — Airflow, Composer & Workflows](../chapters/23-airflow-composer-and-workflows.md)
- [5.5 — Dataform & the Transformation Layer](../chapters/24-dataform-and-the-transformation-layer.md)
- [6.1 — Cloud Data Fusion](../chapters/25-cloud-data-fusion.md)
- [6.2 — Cloud Dataprep](../chapters/26-cloud-dataprep.md)
- [7.1 — Sensitive Data Protection](../chapters/27-sensitive-data-protection.md)
- [7.2 — Compliance, Residency & Encryption](../chapters/28-compliance-residency-and-encryption.md)
- [7.3 — Looker Studio & BI](../chapters/29-looker-studio-and-bi.md)
- [8.1 — ML Foundations on GCP](../chapters/30-machine-learning-foundations.md)
- [8.2 — Prebuilt & AutoML Models](../chapters/31-prebuilt-and-automl-models.md)
- [8.3 — Custom Training & Vertex AI](../chapters/32-custom-training-and-vertex-ai.md)
- [8.4 — BigQuery ML](../chapters/33-bigquery-ml.md)
- [8.5 — End-to-End Capstone](../chapters/34-end-to-end-capstone.md)

## 📖 Further Reading

- [GCP documentation hub](https://cloud.google.com/docs)
- [Google Cloud Architecture Center](https://cloud.google.com/architecture)
- [Google Cloud Skills Boost](https://cloud.google.com/learn/training)
- [GCP Professional Data Engineer study guide](https://cloud.google.com/certification/resources/data-engineer-study-guide)
- [GCP certification exam overview](https://cloud.google.com/certification)
