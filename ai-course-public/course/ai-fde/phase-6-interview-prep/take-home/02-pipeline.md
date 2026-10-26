# Take-Home Project 2 — The Data Pipeline (build a working ETL/ELT pipeline in 4-8 hours)

> **The data-pipeline take-home is the second most common FDE take-home variant.** It shows up at AI companies that ingest customer data (Anthropic, OpenAI, Scale AI, Databricks, Rippling) and at the data-engineering-focused FDE roles. The pattern is the same as `01-prototype.md` (4-criteria rubric: correctness / observability / cost / handoff), but the artifact is a pipeline that ingests → transforms → loads, not a service that answers questions.

---

## Why this module exists

The prototype take-home (`01-prototype.md`) is the most common. The pipeline take-home is the second most common, and it's the right variant when the customer's problem is **data ingestion + transformation + serving**, not "answer questions about my data." The 4-criteria rubric is identical; the artifact is different.

The thesis: **the data-pipeline take-home is the FDE's data-engineering role in miniature.** The candidate who can ship a working pipeline with idempotency, schema evolution, observability, and rollback is signaling they can do the FDE data work. The candidate who ships a one-shot script that runs once and breaks is signaling they can't.

---

## The 4-criteria rubric (same as the prototype)

The rubric is the same. The artifact is different. Apply the 4 criteria to the pipeline.

### Criterion 1: Correctness (the pipeline runs end-to-end)

**The 5 sub-signals:**

1. **The pipeline is idempotent** — running it twice produces the same output. No duplicates.
2. **The schema is documented** — every table has a schema, every column has a type.
3. **The error handling is real** — bad rows are quarantined, not crashed on.
4. **The pipeline is reproducible** — random seeds, env vars, dependencies pinned.
5. **The pipeline is small** — under 1000 lines. A DAG with 5-10 tasks is enough.

**The 3 most common failure modes:**

1. **Not idempotent** — running twice produces duplicates.
2. **No schema documentation** — the interviewer can't tell what the data looks like.
3. **Crashes on bad rows** — one malformed JSON kills the whole pipeline.

### Criterion 2: Observability (the pipeline is measurable)

**The 5 sub-signals:**

1. **Row counts are tracked** — input rows, output rows, dropped rows, error rows. Per task.
2. **Data quality metrics are exposed** — null counts, unique counts, distribution shifts.
3. **Logs are structured** — JSON logs with pipeline_run_id, task_id, row_count, latency.
4. **A dashboard is exposed** — even a simple `metrics.json` file or `/metrics` endpoint.
5. **Alerts are documented** — what triggers a SEV-1, SEV-2, SEV-3.

**The 3 most common failure modes:**

1. **No row counts** — the pipeline runs, but you can't tell if it worked.
2. **No data quality metrics** — the output is silently corrupt.
3. **Print-statement logging** — `print("done")` is not a log.

### Criterion 3: Cost ceiling (the pipeline is sustainable)

**The 5 sub-signals:**

1. **Compute cost is tracked** — for cloud pipelines: $/run, $/month.
2. **The pipeline is incremental** — only processes new/changed rows, not the full dataset every time.
3. **Backfills are explicit** — the candidate can re-run a date range without re-processing the whole history.
4. **A circuit breaker is in place** — when the source API is failing, the pipeline pauses, not crashes.
5. **The cost model is documented** — `COST_MODEL.md` with: rows/day, $/row, $/day, $/month.

**The 3 most common failure modes:**

1. **Full reprocessing every run** — wastes money; the cost ceiling blows up.
2. **No circuit breaker** — when the source API is down, the pipeline crashes.
3. **No cost tracking** — the pipeline uses the API but doesn't know how much it costs.

### Criterion 4: Handoff (the pipeline is operable)

**The 5 sub-signals:**

1. **A runbook is checked in** — `RUNBOOK.md` with: how to run, how to backfill, what to do when X breaks.
2. **The pipeline is scheduled** — cron job, Airflow, Dagster, Prefect, or a simple `while true; do python pipeline.py; sleep 86400; done`.
3. **The rollback is one command** — `make rollback` reverts to the previous version.
4. **The "FDE has left" test passes** — a colleague can pick up the pipeline and operate it without help.
5. **The handoff checklist is documented** — `HANDOFF.md` with: open issues, known limitations, next steps.

**The 3 most common failure modes:**

1. **No runbook** — the pipeline is code, not a service.
2. **No scheduling** — the pipeline runs only when the candidate runs it.
3. **No handoff checklist** — the candidate vanishes after the take-home.

---

## The 4-hour build plan (the timeboxed FDE pipeline)

### Hour 0-1: Scope (the most important hour)

**Goal:** lock scope. One source, one destination, one transformation. Don't build a 5-source, 5-destination, 10-transformation pipeline.

**The 4 sub-tasks:**

1. **Read the prompt carefully.** Note: (a) the source format, (b) the destination format, (c) the time budget, (d) the deliverables.
2. **Pick the "wow" transformation.** The one transformation that, if it works, makes the customer say "I need this." Resist the urge to ship 5.
3. **List the cuts.** Schema migration, CDC, multi-tenancy, real-time (vs batch), streaming. Cut ruthlessly.
4. **Sketch the DAG.** 1-page diagram: source → transform → destination. Don't write code yet.

### Hour 1-2: Build the happy path

**The 4 sub-tasks:**

1. **Set up the repo.** `git init`, `README.md`, `requirements.txt`, `.env.example`, `Makefile`.
2. **Write the source extractor.** 1 file, 50-100 lines. Pull 100 sample rows from the source.
3. **Write the transformation.** 1 file, 50-100 lines. Apply the "wow" transformation.
4. **Write the destination loader.** 1 file, 50-100 lines. Load to a SQLite database or a CSV file.

### Hour 2-3: Add the 4 criteria

**The 8 sub-tasks:**

1. **Correctness:** write 5 pytest tests. Idempotency + schema + bad-row handling.
2. **Observability:** add row counts + data quality metrics + structured logging.
3. **Cost ceiling:** add an incremental mode (only new/changed rows) + a circuit breaker.
4. **Idempotency:** add a "last run" timestamp; skip rows that have already been processed.
5. **Backfill:** add a `--backfill` flag that re-processes a date range.
6. **Schema evolution:** handle missing columns + new columns without crashing.
7. **Eval set:** 20-30 sample rows with hand-labeled expected output.
8. **Cost model:** `COST_MODEL.md` with: rows/day, $/row, $/day, $/month.

### Hour 3-4: Operability + handoff

**The 6 sub-tasks:**

1. **Runbook:** `RUNBOOK.md` with: how to run, how to backfill, what to do when X breaks.
2. **Scheduling:** add a cron job or a simple `while true` loop. Document the schedule.
3. **Rollback:** `make rollback` reverts to the previous version.
4. **Handoff checklist:** `HANDOFF.md` with: open issues, known limitations, next steps.
5. **Final test run:** run all 5 tests + the eval harness. Verify everything passes.
6. **README polish:** the README should be readable in 60 seconds.

---

## The 5 most common data-pipeline take-home prompts

### Prompt 1: "Build a pipeline that ingests [source] and loads to [destination]"

**The minimum viable artifact:**

1. A source extractor (API, S3, GCS, file)
2. A transformation (filter, aggregate, enrich)
3. A destination loader (BigQuery, Snowflake, Postgres, S3)
4. An incremental mode (only new/changed rows)
5. An eval set of 20-30 sample rows with hand-labeled expected output

### Prompt 2: "Build a CDC pipeline from [database] to [destination]"

**The minimum viable artifact:**

1. A CDC extractor (Debezium, Airbyte, Fivetran-style)
2. A schema evolution handler (add column, drop column, rename)
3. A destination loader
4. A backfill mode (re-process a date range)
5. An eval set with schema-change scenarios

### Prompt 3: "Build a RAG ingestion pipeline"

**The minimum viable artifact:**

1. A document parser (PDF, DOCX, HTML, Markdown)
2. A chunker (fixed-size, semantic, sentence-aware)
3. An embedder (OpenAI, Cohere, local)
4. A vector store loader (Chroma, FAISS, Pinecone)
5. An eval set of 20-30 documents with hand-labeled chunks

### Prompt 4: "Build a data quality pipeline"

**The minimum viable artifact:**

1. A source extractor
2. A data quality checker (null counts, unique counts, distribution shifts)
3. A quarantine (bad rows go to a separate table)
4. A destination loader
5. An eval set with 20-30 sample rows including some bad rows

### Prompt 5: "Build a feature pipeline for ML"

**The minimum viable artifact:**

1. A source extractor (events, transactions, etc.)
2. A feature transformer (aggregations, encodings, joins)
3. A feature store loader (Feast, Tecton, or a simple table)
4. An incremental mode (only new rows)
5. An eval set of 20-30 sample entities with hand-labeled features

---

## The 5 data-pipeline anti-patterns (the disqualifiers)

1. **Not idempotent.** Running twice produces duplicates.
2. **No schema documentation.** The interviewer can't tell what the data looks like.
3. **Full reprocessing every run.** The cost ceiling blows up.
4. **No circuit breaker.** When the source API is down, the pipeline crashes.
5. **No scheduling.** The pipeline runs only when the candidate runs it.

---

## The cross-reference: how this maps to the 6 FDE company loops

| Company | Pipeline take-home | Cross-reference |
|---|---|---|
| **Scale AI** | The canonical pipeline take-home (RLHF data ingestion) | Industry standard for the "data pipeline FDE" |
| **Databricks** | The data engineering FDE variant | Industry standard for the "lakehouse FDE" |
| **Anthropic** | Sometimes paired with the prototype take-home | `../company-experiences/anthropic-fde-customer-simulation.md` § 3 |
| **OpenAI** | Sometimes paired with the prototype take-home | `../company-experiences/openai-semantic-search.md` § 2 |
| **Rippling** | The "data integration FDE" variant | `../company-experiences/../README.md` (Rippling report if added) |
| **AWS FDE** | Sometimes the 4-hr work sample is a pipeline | `../company-experiences/aws-fde-customer-simulation.md` § 3 |

---

## The thesis

**The data-pipeline take-home is the FDE's data-engineering role in miniature.** The 4-criteria rubric (correctness / observability / cost / handoff) is identical to the prototype take-home. The artifact is different: a pipeline that ingests → transforms → loads, not a service that answers questions.

**The candidate who can ship an idempotent, observable, cost-tracked, operable pipeline is signaling they can do the FDE data work.** All other signals are noise.

**General prep gets you past the resume screen. Data-pipeline take-home prep gets you past the Scale AI / Databricks / Anthropic data-FDE loop.**
