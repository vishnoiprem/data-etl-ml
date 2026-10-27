# BigQuery Glossary

> Every term used in this course, defined.

---

## A

**Active storage** — Storage for tables accessed in the last 30 days. Priced at $0.02/GiB/month (logical) or $0.04/GiB/month (capacity-optimized).

**Aggregation** — Combining many rows into fewer summary rows (`SUM`, `COUNT`, `AVG`).

**Airflow** — An orchestration tool that schedules and monitors workflows. Available on GCP as Cloud Composer.

**Apache Beam** — An open-source SDK for defining batch and streaming data pipelines. Runs on Dataflow, Flink, Spark, or locally.

**Authorized view** — A view that uses the view owner's permissions and adds a row filter, used for row-level security.

---

## B

**BI Engine** — A BigQuery feature that reserves dedicated compute for eligible queries, making them free and fast. Requires a BI Engine reservation.

**BigLake** — A managed lakehouse service that gives BigQuery's query engine access to open table formats (Iceberg, Delta Lake, Apache Hudi) stored in Cloud Storage.

**BigQuery** — Google's serverless, fully managed data warehouse.

**Block rewrite** — The internal operation BigQuery uses to apply DML. It rewrites whole blocks, which is why `UPDATE` on a large table is expensive.

**Bucket** — A named container in Cloud Storage. BigQuery reads external data from buckets.

---

## C

**Capacity-optimized table** — A table with ~30% cheaper scans but roughly 2× the storage cost. Best for large, infrequently queried data.

**Clustering** — Sorting data by up to 4 columns so queries filtering on those columns read fewer blocks. ~5–20% storage overhead.

**Collation** — The comparison rules for string data. `und:ci` makes comparisons case- and accent-insensitive.

**Column pruning** — BigQuery reading only the columns your query references. The reason `SELECT *` is expensive.

**Composer** — Cloud Composer, Google-managed Apache Airflow.

**Coder** — In Beam, the mechanism that serializes elements between workers.

**Colossus** — BigQuery's distributed, columnar storage layer. It has no NameNode and scales horizontally.

**Cost optimization** — Reducing the bytes BigQuery scans. Almost all optimization reduces bytes scanned.

---

## D

**Dataflow** — Google's managed streaming and batch data processing service, built on Apache Beam.

**Datasets** — Top-level containers in BigQuery, equivalent to schemas in a traditional warehouse. Each dataset has a location, labels, description, and default expiration settings.

**DML** — Data Manipulation Language: `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`. Priced on bytes scanned *and* bytes modified.

**Dremel** — BigQuery's columnar, tree-based execution engine. It reads only the columns needed, in parallel.

**Dry run** — Validating and estimating a query without executing it. Free and exact.

**Datasets and projects** — A project contains datasets; datasets contain tables, views, and materialized views.

---

## E

**Edge** — A BigQuery Storage API read location, provided near the compute reading the data.

**Elastic** — In Dataflow, the ability to add and remove workers based on load.

**Exactly-once delivery** — A Pub/Sub feature that deduplicates redeliveries of the same message. It does not make your sink idempotent.

**Expiration** — Automatic deletion of data after a set period. `partition_expiration_days` and `default_table_expiration_days`.

**External table** — A table that references files in Cloud Storage without copying them into BigQuery.

---

## F

**Field mode** — `NULLABLE` (default), `REQUIRED`, or `REPEATED`. Determines whether a column can be null, must be present, or holds an array.

**Fully qualified name** — `project.dataset.table` — required in scripts where no default dataset is set.

---

## G

**GCS** — Google Cloud Storage. Object storage with an S3-compatible API.

**Graceful decommission** — Dataflow's controlled shutdown of workers during autoscaling.

---

## H

**Hive partitioning** — A directory convention (`key=value/`) that BigQuery maps to partition columns for external tables.

**Hybrid mode** — A Beam streaming mode that also emits periodic batch windows, for accurate long-running aggregates.

---

## I

**IAM** — Identity and Access Management. Controls who can do what to which resources.

**Iceberg** — An open table format for data lakes. Supported by BigQuery via BigLake.

**Idempotent** — An operation that produces the same result whether run once or many times. `exists_ok=True`, deterministic job IDs, and partition-scoped writes are the patterns.

**INFORMATION_SCHEMA** — BigQuery's metadata schema. `SCHEMATA`, `TABLES`, `COLUMNS`, `VIEWS`, `MATERIALIZED_VIEWS`, `JOBS_BY_PROJECT`, `RESERVATIONS`.

---

## J

**Job** — A unit of work in BigQuery: a query, load, extract, or DML statement.

**Job ID** — The unique identifier of a job. Supplying your own deterministic ID gives exactly-once semantics.

---

## K

**Keyframe** — A compressed storage format in BigQuery's columnar storage.

---

## L

**Label** — A key-value pair on datasets, tables, and jobs. The only reliable cost-attribution mechanism.

**Location** — The region where a dataset's data is stored. Immutable after creation.

**Long-term storage** — Storage for data not accessed for 30+ days. Half the price of active storage, with a slower first read.

---

## M

**Materialized view** — A pre-computed, physically stored result of a query against a **single** base table. Refreshed automatically or manually.

**Materialization** — Writing intermediate results to storage. Materialized views are the most common form.

**MERGE** — An upsert: `WHEN MATCHED THEN UPDATE`, `WHEN NOT MATCHED THEN INSERT`. BigQuery's `MERGE` must match on the partition key.

**Monolithic storage** — BigQuery's columnar storage, where each table is stored as a set of compressed column chunks.

---

## N

**Nested field** — A `RECORD` field containing sub-fields. Accessed with dot notation.

**Nesting** — Data structures inside data. `STRUCT` and `ARRAY` in BigQuery.

---

## O

**On-demand pricing** — Pay per TiB scanned, with no minimum commitment. $6.25/TiB.

**Ordinal position** — A column's 1-based index in the schema. Required when doing `ORDER BY` on a column named `order`.

**Organization** — The top level of the GCP resource hierarchy. Projects live inside organizations.

---

## P

**Partition** — A subdivision of a table, usually by date. Pruning skips entire partitions.

**Partition pruning** — BigQuery skipping partitions that a query's filters exclude. The single biggest cost lever.

**Partition decorator** — Syntax to reference a specific partition: `table$20260115`, `table$20260101:20260131`.

**Partition expiration** — Automatic deletion of partitions after N days.

**Pub/Sub** — Google's messaging service. The backbone of the streaming architecture.

**PCollection** — In Beam, a (possibly unbounded) distributed collection of data.

**PTransform** — In Beam, a function from `PCollection` to `PCollection`.

---

## Q

**Query plan** — The execution plan BigQuery builds. View it in the console's "Execution details" tab or via `EXPLAIN`.

**Query cache** — A 24-hour cache of query results. Does not apply to queries with a destination table or to the streaming buffer.

---

## R

**Range partitioning** — Partitioning on an integer column into fixed ranges (`RANGE_BUCKET`).

**Reservation** — A committed capacity commitment for BigQuery slots or BI Engine units.

**Resource Manager** — The GCP service for projects, folders, and IAM.

**Row-level security** — Restricting which rows a user can see. Implemented with authorized views.

**RPO / RTO** — Recovery Point Objective / Recovery Time Objective.

---

## S

**Safe cast** — `SAFE_CAST` returns `NULL` instead of raising an error on invalid input.

**Schema** — The column definitions of a table: names, types, modes, and descriptions.

**Slot** — BigQuery's unit of compute: 1 vCPU + 4 GB RAM. Capacity pricing is priced in slot-hours.

**Snapshot table** — A point-in-time copy of a table. Costs storage immediately.

**Storage Write API** — A high-throughput streaming insert API. Free for the first 2 GB/day/table, then $0.01/GiB.

**Streaming buffer** — The recent-data region of a BigQuery table. Not query-cached, billed at active storage rates.

**Streaming inserts** — Writing individual rows via `insert_rows_json` or the Storage Write API. The first 1 GB/day/table is free.

**Struct** — A grouped set of named fields.

**Super-scalar** — Capable of executing many queries in parallel across many nodes.

---

## T

**Time travel** — Querying a table's state within the last 7 days using `FOR SYSTEM_TIME AS OF`.

**Timestamp** — A date and time with nanosecond precision, always stored in UTC.

**Transaction** — BigQuery supports multi-statement transactions inside `BEGIN ... END` blocks.

**Trigger** — In Beam, the rule that decides when a window's result is emitted.

---

## U

**Undelete** — Restoring a table or dataset deleted within the last 30 days.

**Unit of work** — In Airflow, a single task instance.

---

## V

**View** — A virtual table defined by a query. Expanded at query time; no storage cost.

**VPC Service Controls** — A Google Cloud perimeter that restricts which services and data a principal can access.

---

## W

**Watermark** — Beam's estimate of the point up to which it has received all data for a window. Data after the watermark is "late."

**Wildcard table** — A query over multiple tables matching a pattern, where `_TABLE_ID` identifies the source table.

**Window** — In Beam, a time-bounded grouping of elements. `FixedWindows`, `SlidingWindows`, `SessionWindows`.

---

## X

**XCom** — Airflow's small key-value store for passing values between tasks. For small values only.

---

## Y

**YAML** — A human-readable configuration format, used for Airflow DAG serialization and GitHub Actions.

---

## Z

**Zstandard** — A fast, high-ratio compression codec. The best default for Parquet today.

**Zone map** — Min/max statistics stored per row group, enabling predicate pushdown in Parquet.
