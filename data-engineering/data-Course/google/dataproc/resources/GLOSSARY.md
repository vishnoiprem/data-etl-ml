# Dataproc + PySpark Glossary

> Every term used in this course, defined.

---

## A

**Action** — A Spark operation that triggers a job. `count()`, `show()`, `collect()`, `write()`, and `toPandas()` are actions; `filter()`, `select()`, and `join()` are not. Nothing runs until an action fires.

**Adaptive Query Execution (AQE)** — A Spark 3.x feature that rewrites the physical plan at runtime based on the actual shuffle statistics it observes. It coalesces small shuffle partitions and splits skewed ones. Enabled by default since Spark 3.2; leave it on.

**Autoscaling** — Automatically adding and removing Dataproc **worker VMs** to match demand. It is a cluster-level feature, configured with an autoscaling policy. Distinct from Spark's dynamic allocation, which scales **executors** within the existing VMs.

**Avro** — A compact binary row format with a schema embedded in the file. Spark reads and writes it natively; it is a common source format for DataStreamer and Kafka pipelines.

---

## B

**BigQuery Storage Write API** — A gRPC streaming API for high-throughput inserts into BigQuery. It bypasses the connector's write-to-GCS-then-LOAD-job mechanism. Excellent for streaming; harder to make idempotent than the connector.

**BigQuery connector** — The Spark connector that reads and writes BigQuery. By default it writes Parquet to a temporary GCS bucket and then issues a BigQuery LOAD job. This course uses it for all batch writes.

**Broadcast join** — A join where Spark copies the smaller side of the join into the memory of every executor, avoiding a shuffle. Triggered automatically below `spark.sql.autoBroadcastJoinThreshold` (10 MB by default), or forced with `F.broadcast()`.

**Broadcast variable** — A read-only value distributed to every executor. Used for lookup tables and configuration. `broadcast()` on a large DataFrame will exhaust executor memory.

**Bucket (GCS)** — A named container in Cloud Storage. The unit of IAM scoping for data in Google Cloud, and the target of the BigQuery connector's staging files.

---

## C

**Catalyst** — Spark's query optimizer. It parses the logical plan, applies rule-based optimizations (predicate pushdown, constant folding, column pruning, join reordering), and generates the physical plan. You can see its decisions in `explain()`.

**Checkpoint** — Persisting a DataFrame's lineage so Spark can truncate it. It truncates the plan, making restarts faster and avoiding the exponential-growth problem in long-running jobs.

**Cluster manager** — The component that allocates executor resources to applications. In Dataproc 2.x this is **YARN**.

**Coalesce** — Reducing the number of partitions without a shuffle. `df.coalesce(1)` writes exactly one output file. It cannot be used to increase the partition count, and it can create very large skewed files.

**Columnar storage** — Storing data by column rather than by row. Parquet, ORC, and BigQuery's native format are all columnar. Columnar layouts let a query read only the columns it needs, and compress repeated values within a column far better.

**Common Crawl / NYC Taxi** — The canonical public datasets used for Spark tutorials. Useful for practising without a billing account.

**Compound column** — A Parquet feature where one column's values are stored alongside the paths that produced them, so a query can reconstruct nested structures without decoding the whole thing.

---

## D

**DAG** — Directed Acyclic Graph. In Spark, a job is a DAG of stages: wide transformations create stage boundaries (shuffles); narrow transformations stay inside a stage. In Airflow, a DAG is the workflow definition itself.

**Data lake** — A storage architecture that keeps data in its raw form in object storage, with structure imposed at read time. GCS is a data lake. A data warehouse imposes structure at write time; BigQuery is a warehouse.

**Data lakehouse** — A lake that also supports transactions, schema enforcement, and time travel — Delta Lake, Apache Iceberg, and Apache Hudi on top of object storage.

**Dataproc image version** — The pinned bundle of software on a cluster: Spark, Hadoop, Python, connectors, and system libraries. `2.2-debian12` ships Spark 3.5.3. **Always pin it** — omitting it means the default can change under you.

**Dataproc Serverless** — A managed, fully elastic Spark offering with no cluster to manage. Billed per vCPU-hour with no idle cost. Not covered in depth in this course.

**Dataproc Workflow** — A Dataproc resource that runs a DAG of Spark jobs, with dependencies between them. The DAG is defined in YAML stored in GCS and submitted with `gcloud dataproc workflow submit`.

**Distributed cache** — Spark's `cache()`/`persist()`, which keeps a DataFrame's partition data in memory (or on disk) across multiple actions, so the computation is not repeated.

**Driver** — The JVM process that runs your main program. It builds the DAG, creates tasks, and collects results. **On Dataproc the driver runs on the master node**, so master memory is your driver memory.

---

## E

**Executor** — A JVM process on a worker that runs tasks and holds partition data. Executors are the unit of Spark's parallelism.

**Execution plan** — The DAG Spark builds from your transformations. View it with `df.explain()`.

**External table** — A BigQuery table that references files in Cloud Storage without copying them. Useful for querying Parquet directly.

---

## F

**Fault tolerance** — Spark's ability to recompute lost partitions. Because transformations are declarative and the input is immutable, a lost task is simply re-run from the lineage. This is what makes Spot workers safe for batch jobs.

**FIFO scheduler** — YARN's scheduler that runs applications in submission order. The default in most Dataproc clusters.

**Fair scheduler** — YARN's scheduler that allocates resources fairly across users, so one tenant cannot monopolize the cluster.

---

## G

**GCS connector** — The Hadoop integration that makes `gs://` paths work transparently in Spark. It is pre-installed on Dataproc; you do not need to add a JAR.

**GCS connector (performance)** — The connector has two modes: the Hadoop FileSystem implementation and the new `gcs-connector` library. The latter supports faster list operations and better performance on many-small-file workloads.

**GC overhead** — The time Java spends reclaiming memory rather than doing work. High GC pressure means too little heap or too much data per executor. More executor cores with the same memory makes it worse.

**Governor** — The set of policies that allocate CPU, memory, and disk to a container within YARN.

---

## H

**HDFS** — Hadoop Distributed File System. Dataproc clusters run it, but **this course stores everything in GCS**. HDFS DataNodes live on primary workers only; secondary (Spot) workers cannot host them.

**Hadoop-compatible filesystem** — The `hadoop.fs.FileSystem` abstraction that lets Spark read `gs://`, `s3a://`, and `hdfs://` with the same code.

**High availability (HA)** — A Dataproc cluster mode with three masters and a leader election. Three times the master cost; unnecessary for batch ETL.

**Hive Metastore** — A catalog that stores table definitions and schemas. Dataproc's Spark SQL can read from it, which lets you write Parquet to GCS and still use SQL table names.

---

## I

**IAM** — Identity and Access Management. Controls who may do what to which resource.

**Idempotent** — An operation that produces the same result whether run once or many times. The central property of a well-built pipeline: a retry after a partial failure must be safe.

**Incremental processing** — Loading only the data that changed since the last run, rather than reprocessing everything. Usually keyed on a modification timestamp or a partition date.

**Initialization action** — A script run on every node when the cluster is created. The standard way to install extra Python packages or JARs. Use it instead of `--py-files` for anything with dependencies.

---

## J

**Job (Dataproc)** — A unit of work submitted to the Dataproc Jobs API. Every `gcloud dataproc jobs submit` creates one. It has a lifecycle (`PENDING` → `SETUP_DONE` → `RUNNING` → `DONE`/`ERROR`/`CANCELLED`) and its own logs.

**JVM** — Java Virtual Machine. Spark runs on the JVM. This is why JVM memory settings (`spark.executor.memory`, `spark.driver.memory`) dominate Spark performance.

---

## K

**Kryo serializer** — A fast binary serializer for Java objects. Set `spark.serializer=org.apache.spark.serializer.KryoSerializer` for a meaningful speedup on shuffle-heavy jobs.

**Kaggle / Kaggle API** — A source of public datasets for practice.

---

## L

**Lineage** — The record of where data came from and how it was transformed. In Spark it is the DAG: the derived-data lineage of a DataFrame. In governance, it is the data lineage graph across systems.

**Long-running job** — A job that runs for hours or days — typically a streaming job or a very large batch. It pins the cluster shape, so autoscaling and cluster shutdown must be disabled for it.

---

## M

**Machine type** — The shape of a Dataproc node: vCPU count and memory. `n2-standard-4` is 4 vCPU and 16 GB. The `highmem`/`highcpu` suffixes change the **ratio**, not the absolute amount.

**MapReduce** — The older Hadoop batch programming model. Spark supersedes it for most work; Dataproc still supports `gcloud dataproc jobs submit hadoop`.

**Medallion architecture** — The Bronze → Silver → Gold layering of a data platform. Bronze is raw, Silver is cleaned and conformed, Gold is business-ready. This course adds a Quarantine layer between Bronze and Gold for rejected rows.

**Metadata server** — The GCE metadata service. Every Dataproc node exposes its cluster name, region, bucket, and role there. A driver reads it to discover its own environment without hardcoding configuration.

**Micro-batch** — Processing a small window of streaming data (say, every 30 seconds) as a batch. It trades latency for throughput and is far simpler to reason about than true streaming.

**MLlib** — Spark's machine-learning library.

**Multicast / named tables** — Spark can register a DataFrame as a temporary view so SQL can query it: `df.createOrReplaceTempView("orders")` then `spark.sql("SELECT ... FROM orders")`.

---

## N

**Natural key** — The business identifier from the source system (`product_id`, `order_id`, `provider_npi`). The thing you join on when loading data, as opposed to the surrogate key you join on inside the warehouse.

**Node labels** — YARN tags that restrict where an application can run. Dataproc autoscaling does not work with node labels.

**Non-preemptible / on-demand worker** — A worker VM that Google will not reclaim. Primary workers are on-demand by default.

---

## O

**Optimistic concurrency control** — Spark's approach to concurrent writes to the same partition. The last writer wins, and the loser may see a partial result. Relevant when two jobs write the same output path.

**ORC** — A columnar file format with built-in statistics, compression, and predicate pushdown. Parquet is generally preferred on Dataproc.

**Output committer** — The component that decides how a job's output files are committed. The v1 committer is slow on object storage; the v2 committer is much faster. Set `spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version=2`.

---

## P

**Partition** — A horizontal slice of a dataset. In a DataFrame, a partition is a chunk of rows processed by one task. In BigQuery, a partition is a date-scoped slice of a table.

**Partition pruning** — Skipping partitions that a query's filters exclude. In BigQuery it is the single biggest cost lever; in Spark, it means not listing or reading irrelevant files.

**Persistent cluster** — A long-lived cluster used for development, interactive sessions, or streaming. It bills continuously until deleted. It should **always** have `--delete-max-idle` and `--delete-max-age` set.

**Persistent volume / disk** — A disk attached to a VM that survives a stop. A stopped Dataproc cluster pays for its disks but not for CPU.

**PIVOT** — Rotating rows into columns, turning a (date, category, amount) shape into a (date, category_A, category_B) shape. Spark SQL has a `PIVOT` clause; the older idiom is `groupBy(...).pivot(...).sum(...)`.

**Predicate pushdown** — The optimization of pushing filter conditions down into the scan so irrelevant rows are never read. Visible in `explain()` as `PushedFilters`.

**Preemptible worker** — A Spot VM that Google may reclaim at any time. In Dataproc these are **secondary workers**, they run executors only (no HDFS), and they cost roughly 60–80% less than on-demand. Spark re-runs lost tasks, so preemption costs time, not correctness.

**Primary worker** — An on-demand worker that runs both Spark executors and HDFS DataNodes. The reliable baseline of a cluster's capacity.

**PySpark** — Spark's Python API. Every DataFrame operation is a JVM call under the hood; the Python driver sends plans to the JVM via a Py4J gateway.

---

## Q

**Quarantine** — A holding area for rows that failed validation. The pipeline does not crash and does not silently drop; it routes the bad rows somewhere they can be inspected, counted, and replayed.

---

## R

**RDD** — Resilient Distributed Dataset. Spark's original abstraction: a distributed collection of immutable objects with explicit transformations and actions. Now largely superseded by DataFrames, but still the right choice for unstructured data and fine-grained control.

**RDD lineage** — The chain of transformations that produced an RDD. It is what makes Spark fault-tolerant: a lost partition is recomputed by replaying its lineage.

**Repartition** — Redistributing rows across partitions, by a column (`repartition("date")`) or a count (`repartition(10)`). A repartition by key involves a shuffle; `coalesce` does not.

**Resource Manager** — YARN's component. It allocates containers to applications and schedules them onto nodes.

**Row Number / Rank** — Window functions for ordering within a partition. `row_number()` never ties; `rank()` ties and skips; `dense_rank()` ties without skipping. Choosing the wrong one changes your leaderboard.

---

## S

**SCD Type 1** — Overwrite the dimension row in place. No history. Simple, lossy.

**SCD Type 2** — Keep every version of the dimension row, with `valid_from`, `valid_to`, and `is_current`. This course's dimensions use Type 2 so historical facts can be joined to the attributes that were true at the time.

**Schema inference** — Letting Spark guess a schema from sampled data. Convenient for exploration, dangerous in production: one malformed row can change a column's type permanently.

**Schema evolution** — Handling a source that adds, removes, or changes fields over time. The BigQuery connector has `enableModeCheckForSchemaFields`; Delta and Iceberg have native schema evolution rules.

**Secondary worker** — A Spot/preemptible worker. Executors only, no HDFS. The burst capacity in a cost-conscious cluster.

**Serverless Spark** — Spark without a cluster to manage. Billed per vCPU-hour.

**Shuffle** — The redistribution of data across executors. It happens on joins, group-bys, window functions, and sorts. It is the single most expensive operation in Spark: it serializes, writes to disk, transfers over the network, and deserializes.

**Shuffle partition** — One output partition of a shuffle. Too many and you get tiny tasks with high overhead; too few and you get long-running tasks with no parallelism. `spark.sql.shuffle.partitions` (default 200) sets the initial count; AQE coalesces them afterward.

**Shuffle service** — A per-node service that serves the map output of completed tasks. On Dataproc, it is external by default (a separate container on the master), which lets it survive executor churn.

**Skew** — Uneven data distribution. A join where one key has a million rows and the others have ten makes one task run 100× longer than its peers. AQE's skew-join handling, key salting, or broadcasting the small side all address it.

**Skewed join** — A join whose data distribution is badly unbalanced, usually because one join key is disproportionately common (`NULL`, `"UNKNOWN"`, `"OTHER"`).

**Spark SQL** — Spark's structured-data API: DataFrames, Datasets, and a SQL engine with a Catalyst optimizer. It is the primary tool in this course.

**SparkSession** — The unified entry point to Spark in Spark 3.x. It replaced the separate `SQLContext` and `HiveContext`. A DataFrame is obtained from it.

**Spark Connect** — A gRPC protocol that lets a separate client process drive a remote Spark cluster. It decouples the client from the cluster's JVM version.

**Stage** — A phase of a Spark job separated by shuffle boundaries. Within a stage, tasks are narrow transformations of the same input.

**Staging bucket** — A temporary GCS bucket where the BigQuery connector writes Parquet before issuing a LOAD job. It should have a lifecycle rule that deletes the files after a day.

**Structured Streaming** — Spark's incremental stream-processing engine. It models a stream as an infinite table and maintains state across microbatches.

**Superset / Looker / Tableau** — BI tools that read the `mart` layer. They are the reason the marts are pre-aggregated.

**Surrogate key** — An artificial, warehouse-assigned identifier for a dimension row (usually a dense `INT64`). It is stable across versions, so a fact row never needs updating when a dimension attribute changes.

---

## T

**Task** — The unit of execution in Spark. One task processes one partition of one stage. Tasks are scheduled onto executors.

**Task Scheduler** — The component that assigns tasks to executors. It packs tasks locally when possible (locality-aware scheduling) to avoid network transfer.

**TEMP VIEW** — A temporary named view registered from a DataFrame, visible for the lifetime of the SparkSession.

**Temporary cluster** — A cluster created for a single job and deleted when the job finishes. The economic default for batch ETL: no idle cost, no forgotten cluster.

**Temporary bucket** — A short-lived GCS bucket used as the BigQuery connector's staging area. Separate from your data buckets, with a lifecycle rule.

**Transformation** — A lazy operation that builds a plan without executing it (`filter`, `select`, `join`, `groupBy`, `withColumn`).

**Transformations vs Actions** — Transformations build a DAG; actions trigger its execution. Every action triggers a full recomputation of everything it depends on, unless the data is cached or checkpointed.

**Tungsten** — Spark's code-generation and memory-management layer: whole-stage codegen, which compiles a query plan into a single generated method, and a unified memory manager that uses off-heap memory for sorting and aggregation.

---

## U

**UDF (User-Defined Function)** — A function you write that Spark does not have a built-in for. Python UDFs require the worker to run a Python process, which serializes data across the JVM boundary — expensive. Prefer a built-in function, then a SQL expression, then a Pandas UDF, then a Scala UDF.

**Uniform Resource Identifiers (URIs)** — `gs://bucket/path`, `s3a://bucket/path`, `hdfs://namenode/path`. The scheme tells Spark which filesystem implementation to use.

**User-managed encryption keys (CMEK)** — A customer-supplied key used to encrypt a resource. Supported by GCS and BigQuery.

---

## V

**VPC** — Virtual Private Cloud. The network a Dataproc cluster lives in. Since image 2.2, clusters are provisioned with internal-IP-only addresses by default.

**Vertical scaling** — Making a machine bigger (more vCPU, more RAM). Usually worse value than horizontal scaling for Spark, which is designed to scale out.

**View** — A virtual table defined by a query. No storage cost; expanded at query time.

**Virtual Private Access (Private Google Access)** — The VPC-level feature that lets internal-only instances reach Google APIs without a public IP. Traffic stays inside Google's network.

---

## W

**Watermark** — In Structured Streaming, the declared point beyond which late data is dropped. It bounds how much state the engine must keep.

**Window function** — A function computed over a set of rows related to the current row: `ROW_NUMBER()`, `SUM() OVER (...)`, `LAG()`, `AVG() OVER (... ROWS BETWEEN ...)`. A `PARTITION BY` defines the group; an `ORDER BY` defines the frame's ordering.

**Workflow (Dataproc)** — See **Dataproc Workflow**. A DAG of jobs with dependencies, defined in YAML and stored in GCS.

---

## X

**XCom** — Airflow's small key-value store for passing values between tasks. For small values only — never a DataFrame.

---

## Y

**YARN** — Yet Another Resource Negotiator. The cluster manager that allocates containers to Spark applications. Dataproc 2.x uses YARN; MapReduce v2 was its predecessor.

**YARN application** — One Spark job's request to YARN for resources. On Dataproc, the Dataproc Jobs API job maps roughly to a YARN application.

---

## Z

**ZooKeeper** — A coordination service used by YARN for leader election, node registration, and configuration. Dataproc runs it on the master.

**Zstandard (zstd)** — A fast compression codec with a good ratio. Often the best Parquet compression setting on Dataproc: `spark.sql.parquet.compression.codec=zstd`.
