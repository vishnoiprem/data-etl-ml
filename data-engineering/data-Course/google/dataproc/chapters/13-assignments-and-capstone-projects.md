# 4.1 — Assignments & Capstone Projects

> **Section 4 · Assignments · Lecture 4.1 · 46:56**

## 🎯 What you will learn

- Four graded projects that map directly onto the course's competency ladder
- What each assignment actually tests, and the failure modes that cost points
- A self-assessment rubric so you can grade your own work before anyone else does
- Stretch goals for candidates who want the capstone to be portfolio-grade

---

## 🧠 Concept

Reading Spark tutorials teaches you syntax. Building a pipeline teaches you engineering.

The assignments below are ordered by difficulty and by the competencies they target. They are
deliberately **not** "write a `groupBy`" exercises — every one of them forces you to make a
decision that has no single right answer, because that is what the job actually looks like.

| # | Assignment | Competency tested | Difficulty |
|---|-----------|-------------------|-----------|
| 1 | **E-commerce Daily Aggregations** | Extraction, joins, aggregation, BigQuery sink | ★★☆☆☆ |
| 2 | **Sensor Stream Rollup** | Streaming, windows, state, late data | ★★★☆☆ |
| 3 | **Clickstream Attribution** | Skew, sessionization, incremental correctness | ★★★★☆ |
| 4 | **Capstone: Full-Stack Lakehouse Pipeline** | Architecture, orchestration, quality, cost | ★★★★★ |

💡 **Do them in order.** Assignment 2 assumes you have Assignment 1's instincts about schemas and
sinks. Assignment 4 assumes all three.

⚠️ **All four assignments must be reproducible from a clean checkout.** If the reviewer cannot run
your code with a single documented command, the assignment is not complete, regardless of whether
the output is correct.

---

## Assignment 1 — E-commerce Daily Aggregations

### Brief

An online retailer stores raw clickstream and order events in Cloud Storage as JSON, one file per
hour. Build a PySpark job that produces daily product-category revenue metrics in BigQuery.

**You are given:**

```
gs://YOUR_BUCKET/raw/events/dt=2026-10-15/hour=00/events.json
gs://YOUR_BUCKET/raw/events/dt=2026-10-15/hour=01/events.json
...
```

**Required outputs:**

1. `silver.events` — flattened, typed, deduplicated events in BigQuery, partitioned by `dt`
2. `silver.products` — a product dimension built from the distinct `product_id` values seen
3. `mart.daily_category_revenue` — one row per `(dt, category)` with revenue, orders, units

### Requirements

- Read the raw JSON with an **explicit** schema, not `inferSchema`
- Handle the malformed-record case explicitly (quarantine, do not silently drop)
- Deduplicate on `event_id`; the same event appears in more than one hourly file
- Join to the product dimension to get `category`
- The job must be **idempotent** — running it twice for the same date produces identical results
- Handle backfill: `--run-date` must accept any date, not just yesterday

### Rubric

| Criterion | Points | What earns full marks |
|-----------|--------|----------------------|
| Schema & typing | 20 | Explicit schema; bad numerics use `try_cast`; dates use a stated format |
| Correctness | 25 | Deduplication, joins, and aggregation all reconcile against the source |
| Idempotency | 20 | Re-running produces identical output; documented how |
| Error handling | 15 | Malformed records are quarantined and counted, not dropped silently |
| Code quality | 10 | `main()`, `argparse`, logging, `spark.stop()` in `finally` |
| Documentation | 10 | README with the run command and a sample output |

### Hints

- The `events.json` files contain a nested `payload` object — you will need `explode` or
  `from_json` depending on its shape.
- There are duplicate `event_id`s **across** hourly files, not within one. A `dropDuplicates` after
  the union is correct; a `dropDuplicates` before it is not.
- Reconcile: `sum(revenue)` in the mart must equal `sum(amount)` across valid silver events.

---

## Assignment 2 — Sensor Stream Rollup

### Brief

A fleet of industrial sensors publishes readings to Pub/Sub. Build a Structured Streaming job
that maintains 5-minute and 1-hour rollups per device.

**You are given:** a Pub/Sub topic carrying JSON readings like
`{"device_id": "d-0042", "ts": "2026-10-15T10:03:11Z", "metric": "temp_c", "value": 71.4}`.

**Required outputs:**

1. A streaming DataFrame with a defined event-time watermark
2. A 5-minute tumbling window with per-device aggregates (`avg`, `min`, `max`, `count`)
3. A 1-hour sliding window (30-minute slide) with the same aggregates
4. Late-arriving data handled per an explicitly stated policy
5. A sink that survives restarts (checkpointed)

### Requirements

- Use `withWatermark` — do not rely on processing time
- State your **late-data policy** and justify it in the README
- The streaming job must be restartable without producing duplicate output
- Include a test that feeds a controlled stream of events and asserts the expected window output

### Rubric

| Criterion | Points | What earns full marks |
|-----------|--------|----------------------|
| Event-time correctness | 25 | Watermark set; windows are event-time, not processing-time |
| Late-data policy | 20 | Explicit, justified, and consistently implemented |
| State & recovery | 20 | Checkpointing configured; restart tested |
| Correctness test | 20 | A real test with expected values, not "it ran without error" |
| Code quality | 15 | Structured functions, logging, config-driven thresholds |

### Hints

- `readStream` from Pub/Sub gives you a `data` column with the raw bytes — you need
  `from_json` or a cast.
- Without a watermark, Spark cannot drop old state and memory grows without bound. This is the
  single most common streaming bug.
- Test the pipeline by writing to `memory://` sink and collecting the results — you do not need
  Pub/Sub to test window logic.

---

## Assignment 3 — Clickstream Attribution

### Brief

Reconstruct user sessions from raw clickstream events and attribute conversions to the correct
touchpoints.

**You are given:** raw click events (`user_id`, `event_ts`, `event_type`, `page`, `product_id`,
`order_id`) in GCS.

**Required outputs:**

1. **Sessionization** — group events into sessions by a 30-minute inactivity gap
2. **Attribution model** — implement last-touch and linear attribution per conversion
3. **A comparison** — how much revenue moves between the two models, by channel
4. An **incremental** output: only sessions that changed since the last run

### Requirements

- Sessionization must handle events that arrive **out of order** within the allowed window
- The attribution must handle **multi-touch conversions** (more than one channel)
- The incremental step must be correct under re-runs — no double-counting
- The job must scale to a dataset with a **skewed user distribution** (one user with 10% of events)

### Rubric

| Criterion | Points | What earns full marks |
|-----------|--------|----------------------|
| Sessionization | 25 | Correct gap logic; handles out-of-order events; documented boundary cases |
| Attribution | 25 | Both models correct; multi-touch handled; revenue conservation verified |
| Incremental correctness | 20 | Watermark/checkpoint correct; re-running does not double-count |
| Scale & skew | 20 | Skew strategy identified and justified; demonstrated on a skewed dataset |
| Code quality | 10 | Clear stages, tests for the attribution arithmetic |

### Hints

- Sessionization is a classic **gaps-and-islands** problem. `lag` over `orderBy`, then
  `sum(is_new_session)` over a window, is the idiomatic Spark solution.
- Revenue conservation check: under **linear** attribution, the sum of attributed revenue per
  conversion must equal the conversion's total revenue. Assert this.
- For skew: a single hot user will dominate one partition. Broadcast joins will not help here —
  you need either salting or a separate two-phase aggregation for the hot key.
- The incremental output is where most students go wrong. Think about what "changed" means when a
  session's last event is still inside the session gap — it is *not* final yet.

---

## Assignment 4 — Capstone: Full-Stack Lakehouse Pipeline

### Brief

Design and build a complete, production-shaped batch pipeline for a domain of your choice (retail,
telecom, finance, logistics, healthcare). This is the assignment that mirrors the job.

**Required architecture:**

```
Source (GCS / Pub/Sub / JDBC)
        │
        ▼
  Bronze  ──  raw, append-only, source fidelity, partitioned by ingest date
        │
        ▼
  Silver  ──  typed, deduplicated, conformed, quality-gated
        │
        ▼
  Gold    ──  business-ready marts in BigQuery, serving a defined set of questions
```

**Required components:**

1. **A PySpark job** implementing all three layers, with `argparse` and a `main()`
2. **Orchestration** — a Dataproc Workflow YAML or a Cloud Composer DAG
3. **A quality gate** that blocks the pipeline on a threshold breach
4. **Idempotency** — documented and demonstrated
5. **Observability** — structured logs with row counts per stage, plus a monitoring metric
6. **A cost model** — a written estimate of the monthly cost, with the levers identified
7. **A README** covering architecture, trade-offs, how to run, and known limitations

### Rubric

| Criterion | Points | What earns full marks |
|-----------|--------|----------------------|
| Architecture | 20 | Layers have a clear contract; the medallion split is justified, not cargo-culted |
| Correctness | 20 | Outputs reconcile; edge cases handled; tests present |
| Orchestration | 15 | Real Workflow/DAG that runs; retries and failures considered |
| Quality & idempotency | 15 | A real gate that fails the job; re-runs are safe and proven |
| Observability | 10 | Logs a reviewer can actually use to diagnose a failure |
| Cost model | 10 | Realistic numbers with named levers; a cheap-and-reasonable design |
| Documentation | 10 | Architecture diagram, run instructions, trade-offs, limitations |

### Rubric for the "gold" submission

A top-scoring capstone does three things that separate it from the rest:

- **It states what it chose not to do.** "We did not implement incremental processing because the
  source is 40 MB/day and a full rebuild is cheaper than the complexity" is a stronger answer than
  a silent omission.
- **It has a failure story.** "If the Pub/Sub subscription dies mid-run, the pipeline resumes from
  the checkpoint and reprocesses the affected partition idempotently" beats a claim that it works.
- **It measures.** An actual before/after on one optimization — `explain(True)` output and timing
  before and after — is worth more than three paragraphs of theory.

---

## 🛠️ Hands-On: Self-Assessment

Before submitting, run this checklist against your own work.

### Correctness

- [ ] Output reconciles against the source — totals match, not just row counts
- [ ] Re-running produces **identical** results (hash the output and check)
- [ ] Edge cases are handled explicitly: nulls, malformed records, duplicates, late data
- [ ] Every schema is defined in code, not inferred at runtime

### Operability

- [ ] The job runs with one documented command from a clean checkout
- [ ] Failures produce an actionable error message, not a stack trace
- [ ] Row counts are logged at every stage boundary
- [ ] `spark.stop()` is in a `finally` block
- [ ] The cluster is deleted, or a deletion schedule is set

### Engineering

- [ ] Costs are estimated, and the biggest lever is identified
- [ ] At least one optimization is measured, not assumed
- [ ] The README explains *why*, not just *what*
- [ ] Known limitations are listed

### A 20-minute pre-submission drill

```python
# Run your job twice into two different paths, then compare.
# If these hashes differ, your pipeline is not idempotent.

import hashlib
import subprocess

def run_job(output_path):
    subprocess.run(
        ["python", "main.py", "--output-path", output_path],
        check=True,
    )

def fingerprint(path):
    """Hash the sorted contents of a Parquet output directory."""
    h = hashlib.sha256()
    for f in sorted(Path(path).rglob("*.parquet")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()

run_job("/tmp/run_a")
run_job("/tmp/run_b")

fa, fb = fingerprint("/tmp/run_a"), fingerprint("/tmp/run_b")
print(f"run A: {fa}")
print(f"run B: {fb}")
print("IDEMPOTENT" if fa == fb else "NOT IDEMPOTENT — investigate before submitting")
```

💡 **The idempotency check is the single highest-value thing you can do before submitting.** Most
non-idempotent pipelines fail only on the *second* run, which is exactly when nobody is watching.

---

## 🔑 Key Takeaways

- The assignments test engineering decisions, not syntax — every one has defensible multiple
  answers.
- **Idempotency is the most common failure mode** across all four assignments, and it only shows
  up on a re-run.
- Quarantine is not the same as dropping. "How many records did you discard and why" is a question
  every reviewer asks.
- Skew is a data problem before it is a Spark problem — identify the hot key before reaching for
  `repartition`.
- A cost model with named levers is worth more than a fast cluster.
- Documenting what you deliberately did **not** build is a sign of senior judgment, not an
  incomplete submission.

---

## 📚 Practice Exercises

1. **Rubric audit.** Take your Assignment 1 submission and grade it against the rubric in this
   chapter. Give yourself points. Write down the three criteria where you lost the most and why.

2. **Idempotency torture test.** Add a deliberate non-determinism to your pipeline — remove a
   `F.rand(seed)` call, or add a `collect()`-based ordering — and confirm the fingerprint check
   catches it. Then remove the non-determinism and confirm it passes.

3. **Cost model.** Take Assignment 1 and produce a monthly cost estimate for your design. Name
   the three biggest levers and estimate the saving from pulling each one.

4. **Failure injection.** Kill your Spark job mid-run and restart it. Document what happened, what
   data was duplicated or lost, and what you would change. This is the exercise that separates
   "it worked on my machine" from "it works in production."

---

## 📖 Further Reading

- Dataproc job submission — https://cloud.google.com/dataproc/docs/guides/submit-job
- Dataproc Workflows — https://cloud.google.com/dataproc/docs/concepts/workflows/about-workflows
- Cloud Composer DAGs — https://cloud.google.com/composer/docs/how-to/access-airflow
- Spark structured streaming — https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- Spark SQL performance tuning — https://spark.apache.org/docs/latest/sql-performance-tuning.html
- BigQuery partitioning & clustering — https://cloud.google.com/bigquery/docs/partitioned-tables
