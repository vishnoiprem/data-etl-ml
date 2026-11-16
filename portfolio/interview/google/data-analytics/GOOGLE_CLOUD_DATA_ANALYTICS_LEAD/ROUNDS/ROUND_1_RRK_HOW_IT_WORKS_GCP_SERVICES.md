# How each Google Cloud data service actually works

Companion to `ROUND_1_RRK_TOPIC_DEEP_DIVE.md`. That file lists *what* to know. This one explains *how the thing works inside*, because the RRK interviewer separates people who have run a service from people who have read its product page by asking "why does it behave like that?".

Each section has the same shape:

1. **What it is in one line**
2. **How it works inside** (the mental model that explains its behaviour)
3. **The knobs that matter** (what you actually configure)
4. **Failure modes and gotchas** (what breaks in production, and why)
5. **Say it in 60 seconds** (the spoken version, with `//` pauses)
6. **Probes and answers** (the follow-ups the interviewer uses to test depth)

Services, in the order an interviewer usually walks them: Cloud Storage → Pub/Sub → Dataflow → BigQuery → Dataproc → Datastream → Dataform → Composer → BigLake and Dataplex → Looker → Vertex AI → the app layer (Cloud Run, Cloud Functions, App Engine, Bigtable) → security spine (IAM, VPC Service Controls, CMEK).

---

## 1. Cloud Storage (GCS)

**One line.** Object store. The landing zone for every batch pipeline and the cheapest place data ever sits.

**How it works inside.** Objects are immutable blobs with metadata, addressed by bucket + name. There are no real directories; the "folders" are name prefixes. Writes are strongly consistent: once a PUT returns, every reader sees the new object, including list operations. An object is replaced atomically; you never see a half-written object. Storage classes (Standard, Nearline, Coldline, Archive) change the price per GB versus the price per retrieval, not the API.

**Knobs.** Location (region, dual-region, multi-region) which decides residency and egress; storage class and lifecycle rules (move to Coldline after 30 days, delete after 400); object versioning; retention policies and bucket lock (write-once for audit); uniform bucket-level IAM (turn off per-object ACLs); CMEK.

**Gotchas.**
- **Prefix hot-spotting is gone**, but *listing* a prefix with millions of objects is slow. Partition the names by date: `raw/orders/dt=2026-01-02/part-0001.parquet`.
- **Small files kill downstream.** 100,000 files of 10 KB make BigQuery loads and Spark jobs crawl. Compact to 100 MB to 1 GB files.
- **Egress between regions costs money.** A US multi-region bucket feeding an `asia-southeast1` BigQuery dataset is a load error (location mismatch) and, where it does work, a bill.
- **Default location is US multi-region.** Residency violations start with a bucket someone created without thinking.

**Say it in 60 seconds.**
> GCS is the landing zone. // Immutable objects, strongly consistent, so a file is either there whole or not at all, // which is what makes the write-then-rename pattern safe. // I partition the object names by date so loads and lifecycle rules can target a slice, // keep files between a hundred megabytes and a gigabyte, // and pin the bucket region to the same region as BigQuery so residency and egress are both handled by the layout, not by a review.

**Probes.**
- *How do you make a GCS-to-BigQuery load idempotent?* Load by object list into a staging table keyed by file name and run a MERGE, or load straight into a date partition with `WRITE_TRUNCATE` on that partition decorator. Record the manifest of files loaded, so a rerun loads the same set.
- *Someone deleted a bucket's objects.* Soft delete (default 7 days) and object versioning. If neither was on, it is gone; that is why versioning on raw zones is a default, not an option.

---

## 2. Pub/Sub

**One line.** Global, serverless message bus. Producers publish to a topic; each subscription gets its own copy of every message.

**How it works inside.** A topic is a log of messages replicated across zones in the publish region. A subscription is a cursor plus a per-message acknowledgement state. The service delivers a message to a subscriber, starts an **ack deadline** timer (10 s to 600 s), and if no ack arrives in time it **redelivers**. That is the whole reason Pub/Sub is "at least once": the timer, not a bug. Delivery is **pull** (the client asks, including streaming pull over a long-lived gRPC stream) or **push** (Pub/Sub POSTs to an HTTPS endpoint). Messages are retained for the subscription until acked, up to the retention window (default 7 days, up to 31), and a topic can also keep acked messages for **seek/replay**.

Two features are routinely misdescribed:
- **Ordering keys.** Messages published with the same key, from the same publisher, in the same region, are delivered to a subscriber in publish order. Different keys have no ordering relationship. Throughput per key is limited (about 1 MB/s), so a single key is a bottleneck by design. Order is a property of *delivery to the subscriber*; once a Dataflow pipeline shuffles by a different key, the ordering is gone.
- **Exactly-once delivery.** A pull-subscription setting. It means: once you ack a message, Pub/Sub will not redeliver it, and an ack after the deadline fails rather than silently succeeding. It does **not** deduplicate two messages the producer published twice; those have different message IDs and are, to Pub/Sub, two messages. End-to-end exactly-once still needs a producer-assigned ID and an idempotent sink.

**Knobs.** Ack deadline; retention and `retain_acked_messages`; dead-letter topic with `max_delivery_attempts` (5 to 100); retry policy (immediate vs exponential backoff); message ordering on the subscription; exactly-once on the subscription; filters (subscription delivers only matching attributes); schema on the topic (Avro or Protocol Buffers, with revisions); BigQuery subscription and GCS subscription (write straight to a sink with no Dataflow).

**Gotchas.**
- **Dead-letter topic without a subscription on it** silently drops the dead letters. Create the subscription, and give the Pub/Sub service account publish rights to the DLQ topic and subscribe rights on the source.
- **Push to an endpoint that returns 500** triggers redelivery with backoff; a slow endpoint causes a storm. Pull with flow control is safer for data pipelines.
- **Message attributes vs payload.** Filters only see attributes. Put `event_type`, `tenant`, `schema_version` in attributes so routing does not require decoding.
- **Cross-region.** Publish is global; the message is stored in the nearest region unless you set a message storage policy. For residency, set the policy on the topic.
- **BigQuery subscription** is cheap and simple, but it writes what arrives: no dedup, no transformation, schema must match. Fine for raw append; not a substitute for Dataflow where correctness matters.

**Say it in 60 seconds.**
> Pub/Sub is at-least-once because of the ack deadline. // The service hands you a message, starts a timer, // and if your ack doesn't land in time it sends it again. // So duplicates are a *normal* outcome, not a failure. // Ordering keys give you order per key, per publisher, down to the subscriber, // and the moment I shuffle on a different key in Dataflow that order is gone. // Exactly-once on the subscription stops redelivery after an ack, // but two publishes are two messages. // So I design for a producer-assigned ID and an idempotent sink, // and I always put a dead-letter topic *with a subscriber* on it.

**Probes.**
- *Why not just rely on exactly-once delivery?* Because the producer retries on a timeout and publishes the same event twice with two message IDs. Exactly-once is about the subscription's ack semantics, not about the event.
- *How do you size ordering keys?* Throughput per key is capped around 1 MB/s, so I pick the finest key that still preserves the order the business needs (customer, not country) and measure the hottest key.
- *Seek and replay?* Seek to a timestamp or snapshot re-marks messages as unacked. Downstream must be idempotent, or replay doubles everything.

---

## 3. Dataflow (Apache Beam)

**One line.** Managed runner for Beam pipelines, batch and streaming, with the Beam model of event time, windows, watermarks and triggers.

**How it works inside.** You write a Beam pipeline: PCollections and transforms. Dataflow turns it into a graph, **fuses** adjacent stages that need no shuffle into one stage, and runs the stages on worker VMs. A **shuffle** happens at every GroupByKey or Combine: data is repartitioned by key. In batch, shuffle runs in the Dataflow Shuffle service off the workers. In streaming, **Streaming Engine** holds the per-key state and timers in a service, which is what lets autoscaling shrink and grow without losing state.

The Beam model, which is the part the interviewer is really asking about:
- **Event time vs processing time.** Each element carries an event timestamp. Windows are defined over event time, so results do not depend on when data happened to arrive.
- **Watermark.** The runner's estimate of "all data with event time earlier than X has arrived". It is derived from the source (Pub/Sub message publish time, or a timestamp attribute you name). Windows are considered complete when the watermark passes the window end.
- **Allowed lateness.** How long after the watermark passes a window the runner keeps its state, so late elements can still update the result. Beyond that, **late data is dropped by default**. If you want it, you must route it yourself, before windowing or via a trigger that fires late panes.
- **Triggers and accumulation.** A trigger decides when a pane (a result for a window) is emitted: at the watermark, early (every N minutes), late (on each late element). **Accumulating** panes re-emit the full window total each time; **discarding** panes emit only the delta. Pick accumulating when the sink overwrites (MERGE, upsert), discarding when the sink appends and sums.
- **State and timers.** A stateful DoFn holds per-key state (ValueState, BagState, MapState) and sets timers (event-time or processing-time) to clear it. State without a timer grows forever.

**Exactly-once.** Dataflow checkpoints the per-key state and the position in the source, and deduplicates on Pub/Sub message ID across retries inside the pipeline. The effect is that the *pipeline's internal processing* is exactly-once. The sink decides whether the *output* is: the BigQuery Storage Write API with exactly-once semantics, or an idempotent MERGE.

**Knobs.** Streaming Engine on; autoscaling (max workers; in streaming the scaling signal is backlog and CPU); machine type and disk; `numWorkers`; Flex Templates for reuse; timestamp attribute on the Pub/Sub source; windowing, allowed lateness, trigger, accumulation mode; `withDeadLetterQueue` patterns via TupleTag side outputs; BigQueryIO write method (`STORAGE_WRITE_API`, `STREAMING_INSERTS` legacy, `FILE_LOADS` for batch); runner v2; Dataflow Prime (vertical autoscaling, right-fitting).

**Gotchas.**
- **The watermark is only as good as the timestamp attribute.** If you leave the default, the watermark follows Pub/Sub *publish* time, and a producer that batches for an hour makes every event "late" by an hour.
- **One slow key stalls the watermark** for everyone, because the watermark is the minimum over all pending work. Hot keys and large per-key state show up as system lag.
- **Data freshness vs system lag.** Freshness = how old the newest processed element is. System lag = how long the oldest unprocessed element has waited. Alert on both; one rising with the other flat points to a stuck key or a slow sink.
- **Backlog with autoscaling pinned** usually means the sink is the bottleneck (BigQuery streaming quota, a slow external API), not CPU. Adding workers does nothing.
- **Updating a streaming pipeline** requires compatible transforms (same names). Rename a step and the update fails; you then drain (finish in-flight windows, flush) or cancel (lose in-flight).
- **Side inputs** are reloaded per window and held in memory; a 10 GB side input is a design error, use a lookup (Bigtable) or a CoGroupByKey.
- **Python vs Java.** Python Beam on Dataflow is fine for most pipelines; the heaviest streaming, custom I/O and the best SDK coverage are still Java. Say so if asked.

**Say it in 60 seconds.**
> Dataflow runs Beam, and Beam separates *when the event happened* from *when it arrived*. // Every element carries an event timestamp; // windows are over event time; // and the watermark is the runner's estimate of completeness, // derived from the timestamp I tell it to trust. // Allowed lateness says how long a window stays open after the watermark passes it. // After that, late data is dropped unless I catch it, // so I always send it to a side output and a dead-letter table. // Exactly-once inside the pipeline is checkpointed state plus dedup on message ID; // the *output* is exactly-once only if the sink is idempotent, // Storage Write API or MERGE. // And in streaming, I watch system lag and freshness together; one slow key stalls the watermark for everyone.

**Probes.**
- *Accumulating or discarding, and why?* Depends on the sink. MERGE on window key: accumulating (latest total wins). Append-and-sum: discarding (each pane is a delta). Mixing them double-counts.
- *Reprocess a day?* Streaming: seek the subscription to the timestamp and let idempotent sinks absorb it. Or run the same Beam code in batch mode from the archived raw data in GCS into the same partitioned table, which is the stronger pattern: one codebase, two runners.
- *Why Dataflow over Spark Structured Streaming on Dataproc?* Event-time semantics are first-class in Beam, Streaming Engine autoscaling, no cluster to run. Spark wins when the team is Spark-native and the code already exists.
- *Dataflow is expensive, what do you do?* Streaming Engine on, right-size, turn off unneeded logging, batch where sub-minute latency is not required, and check the sink: a Dataflow job waiting on a slow sink is paying for idle workers.

---

## 4. BigQuery

**One line.** Serverless analytical warehouse: columnar storage separated from a distributed query engine, billed by bytes scanned or by slots.

**How it works inside.** Storage and compute are separate. Data lives in **Capacitor**, a columnar format, on Colossus (Google's distributed file system), replicated and encrypted. A query is compiled into a tree of stages run by **Dremel** on **slots** (units of CPU and memory); stages exchange data through an in-memory shuffle tier. Because storage is columnar, a query reads only the columns it names, which is why `SELECT *` is the most expensive habit in the product. Storage is immutable at the file level; DML (UPDATE, DELETE, MERGE) rewrites the affected storage blocks, which is why BigQuery handles updates in bulk well and row-by-row updates badly.

**Partitioning and clustering.** Partitioning splits a table into segments by a date/timestamp/integer column or by ingestion time; a filter on the partition column lets the engine skip whole partitions (partition pruning). Clustering sorts data within a partition by up to four columns so block-level min/max statistics let the engine skip blocks (block pruning). Partition on the column every query filters on (event date), cluster on the next most common filters and join keys (customer_id, country). `require_partition_filter` forces every query to prune. Partition limit is 10,000 per table, which is why hourly partitioning on a multi-year table runs out.

**Loading and writing.** Three ways in: **batch load** from GCS (free, atomic per job, best for bulk), **Storage Write API** (gRPC streaming with stream offsets; committed type for at-least-once, pending type for atomic batch commit, and exactly-once when you track offsets), and legacy **streaming inserts** (`insertAll` with best-effort `insertId` dedup over a short window; the client library generates a random `insertId` unless you pass `row_ids`, so a rerun does not deduplicate). Streaming data sits in a write-optimised buffer for a short while before being converted to columnar; DML on rows still in the buffer fails.

**Time travel and snapshots.** Every table keeps history for 2 to 7 days (configurable). `FOR SYSTEM_TIME AS OF` reads it, and a dropped table can be undeleted inside the window. Consequence for erasure: a deleted row is still readable for the window, so a PDPA erasure is complete only when the window has elapsed or you set it to 2 days and document it. Table snapshots and clones are copy-on-write, cheap until the base changes.

**Pricing.** On-demand: per TB scanned, with `maximum_bytes_billed` as the guardrail. Capacity: **editions** (Standard, Enterprise, Enterprise Plus) with slot commitments and autoscaling slots; **reservations** assign slots to projects or folders so BI, ETL and ad hoc do not fight. Storage: active vs long-term (untouched 90 days, half price), and logical vs physical billing (physical wins on compressible data). **BI Engine** caches in memory for dashboards. Cached results are free when the exact query repeats and the tables have not changed.

**Governance in the engine.** Column-level security via **policy tags** in Data Catalog (now Dataplex); **row-access policies** filter rows by the caller; **authorised views** and **authorised datasets** let a view read a table the user cannot; **dynamic data masking** on policy tags shows hashed or null values to unauthorised readers. Datasets have a location; a query cannot join across locations.

**Extensions.** **BigQuery ML** trains models in SQL (logistic regression, boosted trees, ARIMA, k-means, plus remote models calling Vertex AI, including Gemini for text). **BigLake** tables read Parquet, ORC, Avro and Iceberg in GCS with the same security model as native tables. **Omni** runs the engine on data in AWS and Azure. **Remote functions** call Cloud Functions or Cloud Run from SQL. **Search indexes** and **vector indexes** for text and embedding lookups. **Continuous queries** for SQL over streaming arrivals. **Change history** via `APPENDS` and `CHANGES` table functions.

**Knobs.** Partition type and column; clustering columns; `require_partition_filter`; partition expiration; `maximum_bytes_billed` on jobs and projects; reservations and assignments; dataset location; default table expiration; time travel window; CMEK on dataset; policy tags; row-access policies; materialised views (auto-refresh and smart tuning: the optimiser rewrites queries to use them).

**Gotchas.**
- **`SELECT *` on a wide, unpartitioned table** is the classic cost spike. Fix with partition filter, column selection, and `maximum_bytes_billed`.
- **DML per row.** A loop of single-row UPDATEs is slow and hits DML concurrency limits. Batch into one MERGE.
- **MERGE with `WHEN NOT MATCHED BY SOURCE THEN DELETE`** against an incremental source deletes everything not in today's batch. Only use it when the source is a full snapshot.
- **JOIN skew.** One hot key (a null customer_id joining millions of rows) makes one slot do all the work; the query shows one stage at 99% forever. Filter nulls, salt the key, or pre-aggregate.
- **Streaming buffer.** Rows just streamed are not DML-able and may be missing from a partition copy for a few minutes.
- **Cross-region queries fail.** Datasets in `asia-southeast1` cannot join `US`. Fix the layout, not the query.
- **Slot starvation.** A reservation shared by ETL and dashboards makes the 9 a.m. board view wait for the 9 a.m. load. Separate reservations, or let ad hoc stay on-demand with a bytes cap.
- **Quotas.** Load jobs per table per day (1,500), DML statements queued per table, API requests per second. Many small loads is an anti-pattern; batch them.

**Say it in 60 seconds.**
> BigQuery separates columnar storage from a distributed engine that runs on slots. // Cost is bytes scanned, so the two levers are *which columns* and *which partitions*. // I partition on the date every query filters by, cluster on the next filters and join keys, // and turn on `require_partition_filter` so a bad query fails fast instead of scanning two years. // For writes, batch loads from GCS are free and atomic; // Storage Write API with offsets gives exactly-once streaming; // legacy streaming inserts only dedupe best-effort. // Time travel keeps deleted rows readable for up to seven days, // which matters the moment someone says "erasure within thirty days". // And governance is in the engine: policy tags for columns, row-access policies for rows, authorised views for the rest.

**Probes.**
- *Why did the bill triple overnight?* Someone pointed a dashboard at a raw table without a partition filter, a scheduled query lost its filter, or a new user is running `SELECT *` in the console. Find it in `INFORMATION_SCHEMA.JOBS` by bytes billed and principal, then cap with `maximum_bytes_billed` and fix the layout.
- *Partition or cluster?* Partition for the column everyone filters on with a bounded cardinality (dates). Cluster for high-cardinality filters and joins. Clustering alone is right when the table is small or there is no natural date.
- *How do you do a slowly changing dimension?* MERGE with a surrogate key, `valid_from`/`valid_to`, and `is_current`; or append-only with QUALIFY ROW_NUMBER to pick the latest. The second is simpler, cheaper and reversible.
- *Reservations or on-demand?* Model from `INFORMATION_SCHEMA.JOBS_TIMELINE` slot usage. Steady, high utilisation: commit a baseline and autoscale the peaks. Spiky, low average: on-demand with caps.

---

## 5. Dataproc (Spark and Hadoop)

**One line.** Managed Spark/Hadoop clusters, and a serverless Spark option. The lift path for an existing Spark estate.

**How it works inside.** A cluster is a master (YARN ResourceManager, HDFS NameNode) and workers (NodeManagers, DataNodes), built from a Dataproc image in about 90 seconds. Jobs are submitted through the Dataproc API, which schedules them on YARN. The thing that changes everything versus on-prem: **storage is GCS, not HDFS**. The GCS connector presents buckets as a Hadoop filesystem, so a cluster can be deleted when the job finishes and the data is still there. That is the **ephemeral cluster** model: one cluster per job or per workflow, created and destroyed by a workflow template or Composer. **Dataproc Serverless** removes the cluster altogether: submit a Spark batch, Google provisions executors, bills per vCPU-second, and tears down. **Dataproc Metastore** is a managed Hive Metastore so the table definitions survive cluster deletion and are shared across clusters and with BigQuery via BigLake.

**Knobs.** Image version; machine types; preemptible/Spot secondary workers (cheap, no HDFS, fine for Spark compute); autoscaling policy (scale on YARN pending memory); enhanced flexibility mode (shuffle data off preemptibles); initialisation actions and custom images; component gateway (Jupyter, Zeppelin, Spark UI); Metastore; Workflow Templates; serverless batch properties (executor count, memory, premium tier for larger executors); Spark BigQuery connector (reads via Storage Read API, writes via direct or indirect mode).

**Gotchas.**
- **Treating the cluster like on-prem.** A long-lived cluster that is 20% utilised is the most common Dataproc cost problem. Ephemeral or serverless, nearly always.
- **HDFS on preemptibles.** Secondary workers have no HDFS; shuffle on them is lost when they are reclaimed. Use enhanced flexibility mode or keep shuffle on primary workers.
- **Small files in GCS** are as bad for Spark as for BigQuery. Compact.
- **Hive Metastore on the master** dies with the cluster. Use Dataproc Metastore.
- **BigQuery connector indirect writes** stage through GCS; make sure the bucket and dataset are in the same region.
- **Serverless cold start** is a minute or two; not for sub-minute SLAs.

**Say it in 60 seconds.**
> Dataproc is managed Spark with one structural difference from on-prem: storage is GCS, not HDFS. // So the cluster is disposable. // I run one cluster per job, or serverless Spark, // put the Hive metastore in Dataproc Metastore so definitions survive, // and use Spot workers for compute. // That is the lift step of a migration: move the Spark jobs as they are, // prove parity, // then modernise the heavy SQL ones into BigQuery, // reading the same Parquet through BigLake so nothing is copied twice.

**Probes.**
- *Why not move straight to BigQuery?* Five hundred Spark jobs with custom UDFs and a 14-month window: a straight rewrite is the riskiest path. Lift keeps the business running; modernisation happens by value, job by job.
- *How do you prove a migrated Spark job is correct?* Run old and new in parallel for a cycle, compare row counts, column checksums and business totals; keep the diff report as the acceptance evidence.

---

## 6. Datastream (change data capture)

**One line.** Serverless CDC from MySQL, PostgreSQL, Oracle, SQL Server and AlloyDB into BigQuery or GCS.

**How it works inside.** Datastream connects to the source (direct, via Cloud SQL proxy or a private connectivity attachment), takes an initial **backfill** snapshot of the tables you select, and then tails the database's **transaction log** (binlog, WAL, redo log). Each change becomes an event with the row image, operation type (insert, update, delete), source timestamp and a log position. Into BigQuery it writes a **staging table** of changes and (in the default mode) keeps a **replica table** current by applying them with a configurable **staleness** (0 to several hours). Lower staleness means more frequent merges and higher BigQuery cost; "append-only" mode writes every change as a row and leaves the merge to you.

**Knobs.** Include/exclude lists; backfill mode (automatic, manual, none); staleness on the BigQuery destination; append-only vs merge mode; dataset per schema or single dataset; private connectivity; GCS destination format (Avro, JSON) for a Dataflow or custom path.

**Gotchas.**
- **Deletes.** In merge mode they are applied; in append-only you must handle `op = 'D'`. Either way, erasure needs the delete to propagate to every downstream mart, not just the replica.
- **Schema changes** at the source arrive as new columns; dropped columns stay. Treat the replica as a bronze layer, not the mart.
- **Backfill of a huge table** loads the source; schedule it, throttle it, or backfill from a dump and start CDC from the log position.
- **Primary keys.** Tables without one cannot be merged; Datastream falls back to append-only for them.
- **Log retention** at the source must cover any Datastream outage, or you need a new backfill.

**Say it in 60 seconds.**
> Datastream reads the database's own transaction log, // so I get every insert, update and delete with its position, // without touching the application. // It backfills, then streams. // Into BigQuery I choose: let Datastream keep a replica with a staleness I set, // or append every change and build the current view myself with QUALIFY on the latest log position. // Deletes are the part people forget: // a CDC delete has to reach every mart, and BigQuery's time travel keeps the row readable for up to seven days, // so the erasure clock runs longer than the MERGE.

---

## 7. Dataform (SQL transformation)

**One line.** Managed SQL transformation in BigQuery: dbt-style models, dependencies, assertions and scheduled releases, inside the BigQuery console.

**How it works inside.** A repository (Git-backed) holds `.sqlx` files. Each declares a type (table, incremental, view, assertion, operation), references other models with `ref()`, and Dataform compiles them into a dependency graph and then into BigQuery jobs in order. **Incremental** tables get a `WHERE` on the last run's watermark and a `MERGE` when you declare unique keys. **Assertions** are SQL that must return zero rows (uniqueness, not-null, custom rules) and fail the run. **Workflow configurations** schedule compiled releases from a Git branch or tag.

**Knobs.** Compilation variables (environment, dates); release configurations (which branch compiles to which schema); incremental strategy and unique keys; assertions and their severity; service account per environment; tags for partial runs.

**Gotchas.**
- **Incremental logic that trusts wall-clock** reprocesses wrong days on a rerun. Drive the watermark from the target table's max partition, not `CURRENT_DATE()`.
- **Full refresh on a 10 TB incremental table** when someone changes a column type. Plan it, cost it, do it off-peak.
- **Views on views on views** push the whole compute into every dashboard query. Materialise the shared layer.
- **One repository for everyone** becomes a merge-conflict queue. One per domain, with a shared sources package.

**Say it in 60 seconds.**
> Dataform is the transformation layer: SQL models with dependencies, incremental MERGEs and assertions, // compiled from Git and scheduled. // I use it for the silver and gold layers, // Dataflow for anything that needs event time or runs continuously, // and Dataproc only where existing Spark code has to live. // The discipline it brings is that tests run in the pipeline: an assertion failure stops the publish, which is how a wrong board number gets caught before the board.

---

## 8. Cloud Composer (Airflow)

**One line.** Managed Apache Airflow for orchestration across services.

**How it works inside.** Composer runs Airflow on GKE: a scheduler that parses DAG files from a GCS bucket and creates task instances for each **logical date** (the data interval the run is *for*, not the wall-clock moment it runs), workers that execute tasks (Celery or Kubernetes executor), a web server, and a metadata database. Each run has a `data_interval_start` and `data_interval_end`; templated variables like `{{ ds }}` carry them into the task. **Catchup** creates a run for every interval between `start_date` and now. Retries re-run the task callable; the operator must be idempotent for that to be safe. Operators for GCP (BigQueryInsertJobOperator, DataflowStartFlexTemplateOperator, DataprocSubmitJobOperator, GCSToBigQueryOperator) call the service APIs; sensors wait on conditions; deferrable operators release the worker slot while waiting.

**Knobs.** Environment size and Composer 2/3 autoscaling; executor; `catchup`; `max_active_runs`; `depends_on_past`; retries and `retry_delay`; SLA miss callbacks; pools to throttle concurrent BigQuery jobs; connections and secrets (Secret Manager backend); Airflow variables for environment config.

**Gotchas.**
- **`datetime.now()` in a task** instead of the logical date. The single most common Airflow bug: a rerun loads the wrong day and a catchup loads today 300 times.
- **`catchup=True` with an old start date** on first deploy schedules hundreds of runs at once.
- **Append plus retries** doubles the data. Load into the partition decorator with truncate, or MERGE.
- **Heavy Python in the worker.** Pulling 50 GB through pandas on a Composer worker is a pattern from laptops. Push the compute to BigQuery or Dataflow; Airflow coordinates.
- **Top-level code in DAG files** runs at every parse, every 30 seconds. A BigQuery query at module scope is a DAG that costs money while idle.
- **Composer is not cheap at idle.** A small environment runs a few hundred dollars a month doing nothing. For simple schedules, BigQuery scheduled queries or Dataform workflows are enough; Composer earns its cost when there are cross-service dependencies.

**Say it in 60 seconds.**
> Composer is managed Airflow, and the concept that matters is the logical date: // a run is *for* an interval, not *at* a moment. // Every task reads its date from the context, never from the clock, // writes to the partition for that date with truncate or MERGE, // and then retries, reruns and backfills are all the same operation and all safe. // Airflow coordinates; BigQuery, Dataflow and Dataproc do the work. // And I only reach for Composer when there is a real cross-service dependency graph; a single chain of SQL is a Dataform workflow.

---

## 9. BigLake, Dataplex and the lakehouse layer

**BigLake.** A table type that lets BigQuery (and Spark, through the BigLake connectors) read open formats in GCS, with BigQuery's security model applied: policy tags, row-access policies, no need to give users bucket access. Metadata caching makes repeated queries fast. **Iceberg support** (BigLake Iceberg tables, and the BigLake metastore) means a Spark job and a BigQuery query can read and write the same Iceberg table with transactional consistency. This is the "do not copy the data twice" layer in a Dataproc-plus-BigQuery design.

**Dataplex.** Governance and catalogue: **lakes, zones and assets** organise GCS buckets and BigQuery datasets by domain; **discovery** scans GCS and registers tables; **data quality** rules (completeness, uniqueness, range, SQL) run as scheduled scans and publish results; **data profiling**; **lineage** captured automatically from BigQuery, Dataflow and Composer jobs; the **catalogue** (formerly Data Catalog) holds business metadata, tags and policy tags; **data product** boundaries for a data-mesh style organisation.

**Gotchas.**
- BigLake external tables are only as fast as the file layout under them. Partitioned Hive-style paths and compacted Parquet, or the "lakehouse" is slow.
- Dataplex quality scans cost BigQuery slots; scope them to the tables that feed decisions.
- Lineage is automatic for Google services and manual for everything else; a Python script that writes a table does not appear unless you emit lineage events.

**Say it in 60 seconds.**
> BigLake lets BigQuery govern data that stays in GCS as Parquet or Iceberg, // so Spark and SQL share one copy with one security model. // Dataplex sits over both: domains as lakes and zones, // quality rules that run on a schedule and publish a score, // lineage captured from the services, // and a catalogue with policy tags that the engine enforces. // That is what "governed self-service" means in practice: the rules live in the platform, not in a document.

---

## 10. Looker and the semantic layer

**How it works inside.** Looker does not hold data. **LookML** defines views (tables and dimensions and measures), explores (join graphs) and models (which connection, which explores). A user builds a query in the UI; Looker generates SQL against BigQuery, runs it, and caches the result (with persistent derived tables, PDTs, as materialised intermediate tables on a schedule or trigger). **Access filters** inject a `WHERE` per user attribute (country, business unit) into every generated query. **Looker Studio** (formerly Data Studio) is the lightweight free tool; it can connect to Looker's semantic layer or straight to BigQuery; **Looker Studio Pro** adds team workspaces and governance. **Looker Modeler** exposes the semantic layer to other tools.

**Gotchas.**
- **Metric sprawl.** Ten dashboards define revenue ten ways. The point of LookML is one definition; enforce it with code review on the model repository.
- **Explores that join everything** generate expensive fan-out SQL. Symmetric aggregates help; a well-shaped star schema helps more.
- **Row-level security in two places.** Either BigQuery row-access policies (enforced for every tool) or Looker access filters (enforced only through Looker). Prefer the engine; add Looker filters for UX.
- **Dashboards that hit raw tables.** Put aggregates and PDTs between the user and 10 billion rows, and BI Engine in front of the dashboards.

**Say it in 60 seconds.**
> Looker is a semantic layer that generates SQL. // The metric is defined once in LookML, // every dashboard inherits it, // and row-level filters are injected from user attributes. // I enforce row security in BigQuery first so it holds for every tool, // and use Looker's layer for the business definitions. // Self-service then means: anyone can explore a governed explore; nobody redefines revenue in a spreadsheet.

---

## 11. Vertex AI

**How it works inside.** A platform of managed pieces: **Workbench** notebooks; **training** (custom jobs on managed compute, or AutoML); **Model Registry** (versions, lineage to the training run); **Endpoints** (deploy a model version to autoscaling nodes behind a prediction API, with traffic splitting for canaries); **Batch Prediction** (score a BigQuery table or GCS files without an endpoint); **Feature Store** (BigQuery as the offline store; an online store serving low-latency feature reads, synced from BigQuery); **Pipelines** (Kubeflow or TFX pipelines as DAGs with cached steps); **Model Monitoring** (skew between training and serving distributions, and drift over time, with alerts); **Vector Search** (approximate nearest neighbour over embeddings); **Model Garden** and **Gemini** models via the API; **Agent Builder** for RAG and conversational apps on your data; **Evaluation** services for generative outputs.

**Gotchas.**
- **Training/serving skew.** Features computed one way in a SQL training set and another way in an online service. Fix: one feature definition, materialised to both offline and online stores.
- **Endpoints cost while idle.** A deployed endpoint bills for its minimum nodes 24/7. Batch prediction into BigQuery is far cheaper when latency is not needed.
- **Monitoring without a baseline.** Drift detection needs the training distribution recorded at training time.
- **Generative outputs with no evaluation set.** A RAG assistant over finance data needs a golden set of questions with known answers and a measured accuracy before anyone trusts it.

**Say it in 60 seconds.**
> Vertex AI is the managed path from data to a served model. // Features come from BigQuery, served online through the feature store, // models are versioned in the registry, // deployed to endpoints with traffic splitting so a new version takes five percent first, // and monitored for skew and drift against the training distribution. // For most analytics use cases I start with BigQuery ML or batch prediction, because an always-on endpoint is a cost decision, not a default. // For generative work, retrieval over governed data plus an evaluation set comes before any demo.

---

## 12. The app layer: Cloud Run, Cloud Functions, App Engine, Bigtable

Where the platform meets applications: serving data out, and taking events in.

**Cloud Run.** Containers on request, scaling to zero and up on concurrency. Stateless. The default for an API that reads BigQuery or Bigtable, a webhook that publishes to Pub/Sub, a BigQuery remote function, or a small service that fronts a Vertex endpoint. **Cloud Run jobs** for run-to-completion tasks. Sidesteps cluster management; needs a container.

**Cloud Functions (now Cloud Run functions).** Single-purpose code triggered by HTTP, Pub/Sub, GCS object events, Firestore, Eventarc. The classic glue: "when a file lands in this bucket, start this Dataflow template" or "when a message arrives, validate and republish".

**App Engine.** The older PaaS; standard environment scales to zero with language runtimes, flexible environment runs containers. Still common in estates; new work goes to Cloud Run.

**Bigtable.** Wide-column NoSQL, single-digit millisecond reads and writes at any scale, keyed by row key. The **online store** for features, counters and time series: Dataflow writes aggregates in, an API reads them out. Design is all about the row key: it decides distribution and the range scans you can do. Hot-spotting on a monotonically increasing key (timestamp first) is the classic mistake; reverse or hash a prefix. Not for ad hoc analytics, no SQL joins (there is a SQL-like query interface now, but it is a key-value store at heart).

**Also in the picture.** **Firestore** for document data behind apps; **Cloud SQL / AlloyDB / Spanner** as the operational databases that Datastream reads from; **Memorystore** for caching; **API Gateway** and **Apigee** in front of data APIs; **Eventarc** to route events between services; **Secret Manager** for credentials; **Cloud Scheduler** for cron triggers.

**Gotchas.**
- **BigQuery as an operational backend.** Seconds of latency, concurrent-query limits, per-query cost. Serve from Bigtable, Firestore or a cache; BigQuery is the source of truth, not the API.
- **A Cloud Function that does the ETL.** Nine-minute (or 60-minute, second gen) timeouts, limited memory, no retries you control. Functions trigger; Dataflow and BigQuery process.
- **Service accounts with keys** for apps. Use Workload Identity Federation or the attached service account; a leaked key is an incident.

**Say it in 60 seconds.**
> The platform ends at an API or an event, not at a table. // Events come in through Cloud Run functions or Pub/Sub; // served data goes out through Cloud Run on top of Bigtable or a cache, // because BigQuery is the source of truth and not the operational backend. // Bigtable is the online store: the row key decides everything, so I design it for the read path. // And every service runs with an attached identity, no keys.

---

## 13. Security and residency spine

**IAM.** Roles bound to principals at organisation, folder, project or resource. Predefined roles over primitive ones; custom roles when a predefined one is too wide. **Service accounts** are identities for workloads; **Workload Identity Federation** lets external systems (GitHub Actions, on-prem, other clouds) impersonate one without a key. Separate service accounts per pipeline so audit logs say *which* job did *what*.

**Organisation policies.** Guardrails that cannot be overridden below: restrict resource locations (residency by policy, not by review), disable service-account key creation, require OS Login, restrict public IPs, domain-restricted sharing.

**VPC Service Controls.** A **perimeter** around projects and services that stops data leaving through the API plane: a BigQuery dataset inside the perimeter cannot be copied to a bucket outside it even by someone with IAM permission. Ingress and egress rules allow specific paths. This is the control that answers "how do you stop exfiltration by an authorised user".

**Encryption.** Everything encrypted at rest by default with Google keys. **CMEK** (Cloud KMS keys you control) for BigQuery datasets, GCS buckets, Pub/Sub topics, Dataflow state, Dataproc disks; needed when the regulator or client wants the ability to revoke access by disabling a key. **Cloud HSM** and **External Key Manager** for stronger assurance.

**Data protection.** **Sensitive Data Protection** (formerly DLP) scans for PII, classifies columns, and de-identifies (masking, tokenisation, format-preserving encryption). **Policy tags** and **dynamic masking** in BigQuery enforce column access. **Access Transparency** and **Access Approval** for regulated workloads: logs of Google staff access, and approval before it.

**Audit.** **Cloud Audit Logs** (admin activity always on; data access logs to enable) exported to a BigQuery sink for retention and query. Who read which table when is a query, not a hope.

**Say it in 60 seconds.**
> Residency and security are policies in the platform, not reviews of designs. // Organisation policy restricts locations so a bucket in the wrong region cannot be created. // VPC Service Controls draw a perimeter so data cannot leave through the API even with permission. // CMEK gives the client a key they can revoke. // Policy tags and row-access policies enforce column and row access in the engine for every tool. // Workloads run as service accounts with no keys, one per pipeline, // and data-access audit logs land in BigQuery so "who read this" is a query.

---

## Putting it together: the reference flow and where each service sits

```
Sources                 Ingest                Process                 Store / Govern              Serve
──────────              ──────────            ──────────              ──────────────              ──────────
Apps, devices  ──────►  Pub/Sub  ──────────►  Dataflow (streaming) ─► BigQuery (partitioned)  ─►  Looker / Looker Studio
Operational DBs ─────►  Datastream (CDC) ───► Dataform (SQL MERGE)  ─► BigLake over GCS       ─►  Cloud Run API ◄─ Bigtable
Files, SFTP ─────────►  GCS landing ────────► Dataproc (Spark lift) ─► Dataplex (quality,      ─►  Vertex AI endpoint / batch
                                                                       lineage, catalogue)
                        ◄──────────────── Composer orchestrates batch; Cloud Run functions glue events ──────────────►
                        ◄──────── IAM + org policy + VPC Service Controls + CMEK + audit logs around everything ───────►
```

Where correctness lives in this picture, since that is the brief's test:

| Concern | Where it is enforced |
|---|---|
| Duplicates | Producer-assigned ID; Dataflow dedup state with a TTL timer; MERGE or Storage Write API offsets at the sink |
| Late and out-of-order data | Beam event-time windows, watermark from a trusted timestamp attribute, allowed lateness sized from measured p99, late side output to a dead-letter table |
| Updates and deletes | Datastream CDC with `op`; QUALIFY on latest log position; deletes propagated to every mart; time-travel window counted in the erasure clock |
| Schema evolution | Pub/Sub topic schema with revisions; additive-only columns; consumer contract tests in Dataform assertions |
| Backfills and restartability | Composer logical date; partition-decorator truncate or MERGE; Beam batch runner over archived GCS with the same code |
| Atomic publication | Write-audit-publish: staging table, Dataform assertions, then swap via view repoint or partition copy |
| Reversible cutover | Shadow run, reconciliation report, view repoint back to the old table on failure |
| Cost | Partition filter required, bytes cap, reservations split by workload, ephemeral Dataproc, Streaming Engine, batch prediction over endpoints |
| Security on the write path | One service account per pipeline, no keys, VPC perimeter, CMEK, policy tags on landing, audit logs to BigQuery |

---

## How to drill this file

1. Pick one service. Read "How it works inside" once. Close the file. Explain it aloud to an empty room in under two minutes. If you cannot explain *why* it behaves the way it does (why Pub/Sub duplicates, why BigQuery hates row-by-row updates, why Dataflow drops late data), read it again.
2. Then read the probes. Answer each aloud before reading the answer.
3. Say the 60-second version with the `//` pauses, timed. Under 70 seconds or cut.
4. Three services a day; the whole file in a week. BigQuery, Dataflow and Pub/Sub are the three the interviewer will certainly go deep on, so do those twice.
