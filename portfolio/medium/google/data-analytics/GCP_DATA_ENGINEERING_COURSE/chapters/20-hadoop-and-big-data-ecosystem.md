# 5.1 — Hadoop and the Big Data Ecosystem

> **Section 5 · Processing & Orchestration · Lecture 5.1 · 8:00**

## 🎯 What you will learn

- Why Hadoop existed: the concrete constraints that made a dedicated distributed filesystem and scheduler necessary
- The HDFS write pipeline, block size, replication, and the single NameNode single point of failure
- The HA NameNode architecture that replaced the original design
- YARN's ResourceManager, NodeManager, ApplicationMaster, and container model
- The MapReduce map/shuffle/reduce phases and why shuffle dominates the cost
- The Hadoop ecosystem: Hive, Pig, HBase, Sqoop, Flume, Oozie, ZooKeeper, Kafka, and Spark
- Why Hadoop on dedicated commodity hardware became an operational liability
- Where Hadoop still wins, where Spark won, and where the cloud replaced both

---

## 🧠 Concept

### The problem Hadoop was built to solve

In 2003, Google published the Google File System and MapReduce papers. The practical problem was not "the data is big." It was that the data was **too big to fit comfortably on one machine**, and the tools available to process it assumed it would fit.

A single rack of commodity servers in 2005 might offer 20 TB of raw disk and 256 GB of RAM. A single relational database had to keep its working set on that machine, impose a schema before ingestion, and was tied to a vendor's storage engine. If the dataset was 100 TB, you bought a bigger vendor appliance or you built something new.

Hadoop's bet was five claims:

1. **Commodity hardware is enough.** Failure is normal, not exceptional. Design for constant, partial failure.
2. **Move computation to the data.** Networks are slow; disks are fast. Run the program where the bytes already are.
3. **Scale horizontally.** Add nodes; do not buy a larger machine.
4. **The filesystem is the primary abstraction.** Data is large, distributed, replicated, and cheap.
5. **A simple, fault-tolerant execution model is enough.** MapReduce exposed only two operations to application developers.

Those claims created the architecture. Almost every later design decision — from block placement to retries to YARN's resource model — follows from them.

### HDFS: the filesystem that assumed disks fail

HDFS stores a large file as a sequence of **blocks**, normally 128 MB in Hadoop 2 and 3. A 10 GB file becomes roughly 80 blocks. Each block is replicated on three different DataNodes by default.

The reason for large blocks is amortisation. Metadata is stored in memory on the NameNode, while data lives on disk. If blocks were 4 KB, the NameNode would need metadata for millions of blocks per terabyte and its heap would explode. At 128 MB, a petabyte needs about eight million blocks — manageable.

Replication is not backup; it is **availability**. A block survives until its replication count falls below a threshold. A DataNode reports heartbeats to the NameNode. If it stops, the NameNode marks its blocks as under-replicated and instructs other DataNodes to copy them. Recovery begins without human action.

#### The write pipeline

A client writing a file follows a specific sequence:

1. The client asks the NameNode for a list of DataNodes to write each block.
2. The client creates a socket to the first DataNode.
3. The client sends the block to that DataNode.
4. That DataNode forwards the packet to the second DataNode, which forwards to the third.
5. Each DataNode acknowledges receipt back down the chain.
6. The client asks the NameNode to commit the block and close the file.

The write path is a **pipeline**, not a broadcast. Data moves once across the network and is replicated en route. The client acknowledges only after all three replicas have the data.

#### The read pipeline

A reader contacts the NameNode, which returns the DataNodes holding the requested blocks, ordered by proximity. The reader then connects directly to the closest replica and streams data. The NameNode never carries payload bytes; it is metadata and rendezvous only.

#### The NameNode single point of failure

This design creates one obvious weakness. The NameNode holds the namespace, the block-to-DataNode mapping, and the permissions. If it dies, the cluster cannot serve reads or accept writes.

Original Hadoop solved this with a **secondary NameNode** that periodically pulled the namespace and edits log from the active NameNode and produced a checkpoint. That was misunderstood for years: the secondary NameNode was **not** a hot standby. If the primary failed, there was an outage while an operator promoted the secondary, and the secondary lagged by the checkpoint interval. Data written since the last checkpoint could be lost.

Hadoop's real HA fix arrived in **HDFS High Availability** in Hadoop 2:

- Two NameNodes run: one **active**, one **standby**.
- They use a **JournalNode** quorum (normally three) to share the edit log.
- Every namespace mutation is written to the JournalNodes and fsynced before the client is acknowledged.
- The StandbyNode continuously consumes the journal and maintains a current namespace image.
- A **ZooKeeper-based automatic failover** detects the active NameNode's failure and promotes the standby.
- The client uses a configured failover provider to locate whichever NameNode is active.

The key change is durability moved out of the NameNode's local filesystem and into a replicated write-ahead log. The standby NameNode is a genuine replacement, not a checkpoint artifact.

> **Naming precision:** the architecture has one active NameNode and one standby. The **JournalNode** is the replicated edit-log quorum. The **DataNode** stores blocks. Naming these incorrectly is a reliable sign that someone has only read a diagram.

### YARN: resource management separated from the programming model

MapReduce v1 was a single system that did both scheduling and computation. YARN split them.

YARN has three architectural roles:

- **ResourceManager (RM)** — cluster-wide authority. It allocates resources, but it does not run user code.
- **NodeManager (NM)** — one per worker node. It launches and supervises containers, reports node health and resource utilisation to the RM, and handles container lifecycle on behalf of an ApplicationMaster.
- **ApplicationMaster (AM)** — one per application. It asks the RM for containers, defines the execution plan, monitors progress, and handles application-level failures.

A **container** is an allocation of CPU and memory on a NodeManager in which a task runs. Containers are the unit of scheduling and the unit of enforcement. A user application cannot exceed the memory it requested without risking an out-of-memory kill; a container cannot address resources outside its allocation.

The scheduling path is:

```text
application → ResourceManager
                 │  request capacity
                 ▼
          ApplicationMaster
                 │  request containers
                 ▼
             ResourceManager
                 │  grant containers
                 ▼
        NodeManager → container → task
```

The ResourceManager includes a pluggable **scheduler**, most commonly the Capacity Scheduler or the Fair Scheduler. The scheduler decides which application receives which resource. Capacity Scheduler divides the cluster into queues with guaranteed minimums and maximums; Fair Scheduler allocates to applications by recent usage.

YARN is not an elegant API. Application lifecycle, resource types, container monitoring, and failure semantics are complex. That complexity is the price of decoupling execution from scheduling, and it is precisely what made Spark-on-YARN, Flink-on-YARN, and custom YARN applications possible.

### MapReduce: the model that made Hadoop simple

MapReduce expresses a parallel computation as three phases.

**Map.** The input is split into fixed-size chunks. For each chunk, the framework calls the user's `map` function on each key-value pair and emits intermediate key-value pairs.

**Shuffle.** This is the phase everyone underestimates. The framework:

1. Partitions map output by key using a partitioner.
2. Sorts each mapper's output locally.
3. Spills sorted runs to local disk.
4. Merges the runs into one sorted file per reducer.
5. Transfers the reducer's partition from every mapper to the reducer, over the network.
6. Merges the arriving files into one sorted stream.

**Reduce.** The framework groups the shuffled values by key and calls the user's `reduce` function for each key and its list of values.

MapReduce's genius is that developers write two functions and the framework handles scheduling, data locality, failure, and shuffling. Its weakness is that it forces a rigid shape. Intermediate results cannot be reused across jobs, iteration is slow, and every job is a separate YARN application with its own startup cost.

#### Why shuffle is the bottleneck

Shuffle is expensive because it combines three costly operations:

- **Serialization.** Every intermediate record is serialised and deserialised.
- **Disk I/O.** Mappers spill to local disk to bound memory, and reducers read those files.
- **Network transfer.** Data moves between nodes.

The local reduce optimisation helps: if a key's values all land on one mapper, that mapper can reduce them locally. But in a typical job with skewed or high-cardinality keys, most keys still cross the network.

A useful diagnostic: if a Spark or MapReduce job spends most of its time in a shuffle-heavy stage and has no skew in its key distribution, the problem is usually **too few reducers** or **too much data per reducer**. If one reducer dominates, it is **skew**. These have different fixes, and conflating them wastes days.

### The Hadoop ecosystem

Hadoop's value was never only MapReduce. The surrounding projects turned it into a platform.

| Project | Purpose | Why it mattered |
|---|---|---|
| **Hive** | SQL-like interface over files in HDFS | Let analysts and engineers use SQL instead of Java; metastore and SerDe became ecosystem standards |
| **Pig** | Data-flow scripting language | Expressed ETL as a graph of operators; predecessor to Spark's higher-level APIs |
| **HBase** | Random-access, strongly consistent key-value store on HDFS | Low-latency reads and writes for operational lookup tables, not batch scans |
| **Sqoop** | Bulk import/export between relational databases and HDFS | Moved legacy RDBMS data into the lake |
| **Flume** | Ingestion of event streams into HDFS | Early streaming ingestion framework |
| **Oozie** | Workflow scheduling on Hadoop | DAG-based coordination of Hadoop jobs, often with Hive and Sqoop steps |
| **ZooKeeper** | Coordination service | Leader election, distributed locks, and configuration management; later used by HBase, Kafka, and YARN HA |
| **Kafka** | Distributed event log | Durable, partitioned, replayable messaging; increasingly the successor to Flume and the boundary between Hadoop and streaming |
| **Spark** | General-purpose cluster computation | In-memory iterative computation and a richer API, running on YARN, Mesos, or standalone |

Two observations matter:

- Hive, Pig, and Spark all answer the same question — how do you express transformations? — with different trade-offs. Hive with Tez moved away from MapReduce toward DAGs, which is essentially what Spark popularised.
- ZooKeeper and Kafka did not need the HDFS storage model. They set replicated logs and coordination on their own. This is the pattern that led to the modern cloud: **specialise the system for its access pattern**.

### The problems with Hadoop on its own hardware

#### Low utilisation

A Hadoop cluster is provisioned for the **peak batch window**. If the daily ETL finishes in four hours but the cluster was sized for a 24-hour workload, most machines sit idle for 20 hours. Storage and network are provisioned similarly.

The economic consequence is severe. Hadoop's design goal was to make commodity hardware sufficient. But underutilised commodity hardware is still expensive, and it is expensive in a way that does not appear in a per-node line item: hardware refresh cycles, three-year depreciation, cluster consolidation, and rack-level redundancy all assume steady utilisation.

#### Operational burden

A self-managed Hadoop cluster is several distributed systems wearing one name:

- OS and JDK patching across hundreds of nodes
- ZooKeeper quorum management
- HDFS balancing and under-replicated block recovery
- YARN queue configuration and admission control
- Kerberos and Ranger/Hive authorisation
- Spark, Hive, and Tez version compatibility
- Log aggregation and on-call rotation for a system with unusual failure modes

Most organisations discovered that the total cost of ownership of Hadoop exceeded the savings against a managed warehouse and managed compute.

#### The "data gravity" trap

Once data is in HDFS, moving it is expensive and slow. Clusters accumulate stale copies, departed datasets, and multiple formats. Without rigorous metadata management, HDFS becomes an expensive, confusing dumping ground — the phenomenon known as the "data lake" failure mode.

### The honest verdict

**Where Hadoop still wins:**

- Massive-scale batch ETL where the data is genuinely petabyte-scale and mostly sequential reads.
- Workloads on genuinely cheap hardware, in environments where cloud egress or commitment pricing is unattractive.
- Fault-tolerant long-running jobs that must survive node loss without restarting from scratch.
- Existing estates with deep Hive, HBase, or Sqoop investment where migration cost exceeds benefit.

**Where it lost:**

- Interactive and iterative analytics. Spark's in-memory execution and Tungsten memory model beat MapReduce decisively.
- Unstructured and semi-structured data. The Hadoop ecosystem spent years retrofitting JSON and Avro onto a format designed for rows of bytes.
- Operational simplicity. Cloud managed services absorbed the operational burden that killed many Hadoop programmes.
- Streaming. Flink, Spark Structured Streaming, Kafka Streams, and Beam/Dataflow all do it better.

**Where the cloud replaced it:**

Managed services did not merely make Hadoop easier. They changed the unit of purchase from "cluster" to "work performed." You rent vCPU-hours for a batch job and the cluster exists only while the job runs. Storage is a separate metered service. You stop operating a filesystem and start operating a query engine.

This is why the rest of Module 5 focuses on **Dataproc, Dataflow, Composer, and Dataform**. Hadoop is still the intellectual foundation — partitioning, locality, shuffle, and resource scheduling are the ideas that survive — but you should not plan a new Hadoop deployment on GCP. You should understand why the platform's managed services exist.

### Mapping Hadoop ideas onto the course simulator

The course simulator is deliberately small, but its operations are the same primitives Hadoop scaled:

| Hadoop concept | Course simulator equivalent | Why it maps |
|---|---|---|
| MapReduce map stage | `validate_event` on each row | Per-record transformation |
| MapReduce shuffle and reduce | `aggregate_events` | Group and aggregate by key |
| Combiner optimisation | `aggregate_by_window` | Partial aggregation before the expensive phase |
| HDFS block and partition | `partition_for_date` | Deterministic placement by date |
| Replication and idempotency | `deduplicate` | Retry-safe write semantics |
| YARN application | `project.run_pipeline` | A scheduled unit of work |
| Hive SQL aggregation | `render_summary_csv` | A declarative output of the grouped result |

---

## 🛠️ Hands-On

### Exercise 1: inspect Hadoop's descendants in the service catalog

```python
import sys
sys.path.insert(0, "project/core")

from service_catalog import SERVICES, get_service, regions_for

for service_id in ("dataproc", "dataflow", "composer", "dataform"):
    service = get_service(service_id)
    print(service.id, "|", service.name, "|", service.data_role)
    print("   summary:", service.summary)
    print("   regions:", len(regions_for(service_id)))

print("catalog size:", len(SERVICES))
```

Expected shape:

```text
dataproc | Dataproc Managed Apache Spark, Hadoop and Hive on GKE or Compute Engine. | batch
   summary: Managed Apache Spark, Hadoop and Hive on GKE or Compute Engine.
   regions: 12
dataflow | Dataflow Managed runner for Apache Beam batch and streaming pipelines. | streaming
   summary: Managed runner for Apache Beam batch and streaming pipelines.
   regions: 12
composer | Cloud Composer Managed Apache Airflow for workflow scheduling and orchestration. | orchestration
   summary: Managed Apache Airflow for workflow scheduling and orchestration.
   regions: 12
dataform | Dataform Transformation logic as SQL models with tests and lineage. | transform
   summary: Transformation logic as SQL models with tests and lineage.
   regions: 12
catalog size: 40
```

### Exercise 2: reproduce a MapReduce-style aggregation

`aggregate_events` is the reduce half. The map half is `validate_event`, applied independently to every row. No row depends on another, so the map phase parallelises perfectly — exactly like a Hadoop mapper.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events, render_summary_csv

with open("sample_data/events.csv", encoding="utf-8") as handle:
    lines = handle.read().splitlines()

accepted, rejected = ingest_events(lines)
summary = aggregate_events(accepted)

print(f"map output rows: {len(accepted)}")
print(f"rejected rows:   {len(rejected)}")
print(render_summary_csv(summary))
```

Output:

```text
map output rows: 4800
rejected rows:   0
region,event_count,revenue_eur
AMER,1238,464848.02
APAC,1159,421049.85
EMEA,1176,432544.17
LATAM,1227,445554.36
```

The total accepted count is 4800. The four reduce keys are `AMER`, `APAC`, `EMEA`, and `LATAM`.

### Exercise 3: make the shuffle visible

The shuffle moves grouped rows between logical stages. `aggregate_by_window` performs a partial grouping by hour before the final reduce by region, mirroring a combiner.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_by_window, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

windows = aggregate_by_window(accepted)
print("window rows:", len(windows))

by_region = aggregate_events(accepted)
revenue_from_windows = sum(row["revenue_eur"] for row in windows)
revenue_direct = sum(values["revenue_eur"] for values in by_region.values())

print(f"window revenue: {revenue_from_windows:.2f}")
print(f"direct revenue: {revenue_direct:.2f}")
print("identical:", abs(revenue_from_windows - revenue_direct) < 0.01)
```

Output:

```text
window rows: 96
window revenue: 1763996.40
direct revenue: 1763996.40
identical: True
```

The 96 rows are 24 hourly windows × 4 regions. The totals agree because the grouping is associative.

### Exercise 4: demonstrate the skew failure mode

A skewed key concentrates a disproportionate share of one reducer's work. The simulator can show the mechanism directly.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, aggregate_events

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

counts = {
    region: int(values["event_count"])
    for region, values in aggregate_events(accepted).items()
}

mean = sum(counts.values()) / len(counts)
print("mean per key:", mean)
for region, count in sorted(counts.items()):
    print(f"{region:6s} {count:5d}  ratio={count / mean:.3f}")

print("max/min ratio:", max(counts.values()) / min(counts.values()))
```

The ratio is close to 1.0, so no reducer is strangled. Now imagine a source where `region` is always `AMER`: the mean drops, the `AMER` ratio explodes, and that single reduce task becomes the critical path. The fix is **salting** — adding a random prefix to a skewed key so it distributes across many reducers, followed by a second aggregation over the salted key.

### Exercise 5: compare the cost of managed compute versus managed warehouse

The course cost model makes the economic argument for the cloud explicit.

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import compare_architectures, format_comparison

options = compare_architectures(
    scanned_tb=1.0,
    partition_factor=0.01,
    streaming_hours=24,
    batch_runs=1,
)
print(format_comparison(options))
```

The unpartitioned BigQuery scan is the dominant cost. A query that reads the whole table pays for the whole table; a partitioned query that prunes to one day reads one percent of it. This is the same insight Hadoop delivered through HDFS block locality: **do not read what you do not need**. Partitioning is the modern replacement for designing around block placement.

### Exercise 6: model a Hadoop-style cluster with the platform simulator

```python
import sys
sys.path.insert(0, "project/core")

from platform_sim import build_demo_project, format_resource_tree, format_pipeline_log

project = build_demo_project()
print(format_resource_tree(project))
result = project.run_pipeline(open("sample_data/events.csv", encoding="utf-8").read().splitlines())
print(format_pipeline_log(result))
```

This is the managed analogue of a YARN application: one coordinated unit of work with an explicit dependency order, running against a simulated project with IAM, resources, and cost.

### Exercise 7: inspect HDFS-like placement decisions

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    partition_for_date,
    partition_for_event,
    filter_rows_for_partition,
    deduplicate,
)

with open("sample_data/events.csv", encoding="utf-8") as handle:
    accepted, _ = ingest_events(handle.read().splitlines())

target = "20260115"
target_rows = filter_rows_for_partition(accepted, target)
print("partition:", partition_for_date("2026-01-15"))
print("rows in partition:", len(target_rows))
print("sample event partition:", partition_for_event(accepted[0]["event_dt"]))

duplicated = target_rows + target_rows[:100]
cleaned = deduplicate(duplicated, partition=target)
print("after dedup:", len(cleaned))
```

The output shows that all 4800 events land in the `20260115` partition, and that replaying rows through `deduplicate` produces the same 4800 rows. That is the property that makes an at-least-once delivery system safe: retrying a write must not change the result.

---

## 🛠️ Common Errors and Fixes

### 1. `java.io.IOException: All datanodes are bad`

```text
java.io.IOException: All datanodes are bad
    at org.apache.hadoop.hdfs.DFSOutputStream$DataStreamer.setupPipelineForAppendOrRecovery(DFSOutputStream.java:1208)
```

**Cause.** The client could not reach any DataNode holding the intended replicas. In practice this means the DataNodes are down, the network or firewall is blocking the data port (usually 50010), or the client and cluster are on incompatible networks.

**Fix.** Check DataNode liveness in the NameNode UI, confirm the data transfer port is open between all nodes, and verify the client is talking to the intended cluster by checking the `fs.defaultFS` setting. On Dataproc, equivalent symptoms usually mean the cluster is degraded or the worker nodes are being preempted; inspect the Dataproc cluster page and the Compute Engine instance group.

### 2. `Could only obtain replication: 1` or `There are 0 datanode(s) running`

```text
org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.hdfs.protocol.RecoveryInProgressException):
There are 0 datanode(s) running and no exclude files are specified.
```

**Cause.** The NameNode has no live DataNodes, or not enough of them to satisfy the replication factor. A common variant is replication set to 3 on a two-node cluster.

**Fix.** Restore the DataNodes, and either reduce `dfs.replication` to match the number of healthy nodes or add nodes. For a development cluster, set replication to 1 — but understand that you are trading durability for convenience and should never ship that to production.

### 3. `NameNode is in safe mode`

```text
org.apache.hadoop.hdfs.server.namenode.SafeModeException:
Cannot create file/user/... Name node is in safe mode.
```

**Cause.** The NameNode entered read-only safe mode at startup and is waiting for DataNodes to report sufficient blocks. Safe mode can also be left stuck if a DataNode is unhealthy or a block report is delayed.

**Fix.** Wait while the console shows the safe-mode extension count falling. If it does not progress, inspect DataNode logs and block reports. To leave safe mode manually after confirming data health, use `hdfs dfsadmin safemode get` to check and `hdfs dfsadmin safemode leave` to exit. On Dataproc, delete and recreate the cluster instead of reaching into internals.

### 4. YARN application rejected: resource limit

```text
YARN application application_1700000000_0001 failed due to
AM container allocation failed: exceeds queue's current maximum usage limit.
```

**Cause.** The ApplicationMaster requested more memory than the queue's maximum allocation allowed. YARN compares the request to the queue's `maximum-capacity` and to `yarn.scheduler.maximum-allocation-mb`.

**Fix.** Reduce the ApplicationMaster and executor memory settings so the first container fits the queue, raise the queue's maximum capacity, or request a different queue. The common mistake is lowering only the executor memory while leaving the ApplicationMaster heap above the queue maximum.

### 5. `Container killed by YARN for exceeding memory limits`

```text
Container killed by YARN for exceeding memory limits. 5.5 GB of 5 GB physical memory used.
```

**Cause.** A container exceeded its declared memory allocation and the NodeManager killed it. Often the JVM also overshoots because the heap plus off-heap memory exceeds the container limit.

**Fix.** Increase the container allocation and lower the JVM heap so that heap plus overhead fits inside it. For Spark on YARN, the rule of thumb is `spark.executor.memory` around 80 percent of the container memory. Do not merely raise `spark.executor.memory` — that makes the overshoot worse.

### 6. Secondary NameNode mistaken for high availability

```text
Standby NameNode is not automatically failover capable.
The cluster has not been configured for automatic failover.
```

**Cause.** The operator assumed a configured secondary NameNode provided automatic failover. The secondary is only a checkpoint producer unless `dfs.ha.automatic-failover.enabled` is true and the failover provider is configured with the correct ZooKeeper quorum.

**Fix.** Configure the HA architecture properly: two NameNodes, a JournalNode quorum, ZKFC on both NameNodes, and automatic failover enabled. Verify with `hdfs haadmin -getAllServiceState` that the service state is `active`/`standby` rather than `standby`/`standby`.

---

## 💡 Production Notes

- **Run at least three DataNodes and three JournalNodes.** Quorums need an odd number so a majority can be formed without split brain. Two is not a quorum; three is the minimum practical size.
- **Keep HDFS block placement balanced.** Run the balancer and monitor under-replicated block counts. Imbalance often indicates a hot DataNode set or a misconfigured rack topology.
- **Set replication per data temperature.** Three replicas for everything is wasteful for cold data and insufficient for critical data. Replication is a policy decision, not a constant.
- **Do not treat YARN queues as decoration.** Map queue names to teams and products, set guaranteed minimums, and set maximums so one noisy tenant cannot consume the cluster.
- **Measure shuffle bytes, not just job duration.** Shuffle bytes per stage and reducer skew are the two metrics that predict MapReduce and Spark job pain. A Spark UI stage page gives both.
- **Pin library versions in the Hadoop ecosystem.** Hive, Tez, Spark, and Hadoop have a narrow compatibility matrix. Keep the application jar, not the cluster, as the unit of versioning, and rebuild when the base image changes.
- **Know the recovery objective of a NameNode failover.** HA with a JournalNode quorum gives you a fast, planned failover. It does not protect against a corrupt namespace image. Take and copy off-cluster checkpoints.
- **Prefer managed services for new work.** On GCP, Dataproc and Dataflow absorb the NameNode, YARN, ZooKeeper, and cluster-lifecycle burden that dominated Hadoop operating cost for a decade.

---

## 🔑 Key Takeaways

- Hadoop's architecture followed from five assumptions: commodity hardware, data locality, horizontal scale, filesystem-centric design, and a deliberately minimal computation API.
- HDFS stores large replicated blocks; the NameNode stores metadata only. The original single NameNode was a single point of failure, and real HA came from a JournalNode quorum plus a standby NameNode and ZooKeeper failover — not from a secondary NameNode.
- YARN separated resource management from execution: ResourceManager, NodeManager, ApplicationMaster, and containers. This decoupling is what allowed Spark and Flink to run on Hadoop.
- MapReduce's map/shuffle/reduce shape is simple because the framework handles scheduling and failure. The shuffle is expensive because it serialises, spills to disk, and transfers across the network. Diagnose shuffle volume and reducer skew separately.
- The ecosystem was Hadoop's real contribution: Hive for SQL, Pig for flow scripts, HBase for random access, Sqoop for RDBMS transfer, Flume for ingestion, Oozie for workflows, ZooKeeper for coordination, Kafka for logs, Spark for general computation.
- Dedicated Hadoop clusters suffered from peak-sized idle capacity and an immense operational burden. Managed cloud services changed the unit of purchase from cluster to work performed.
- Hadoop still wins for petabyte-scale batch ETL on genuinely cheap hardware with large sunk investment. It lost to Spark for iteration, to specialised cloud services for operations, and to the warehouse-plus-partitioning pattern for analytics.
- The durable ideas are locality, partitioning, replication, idempotency, and scheduling. These survive even when the Hadoop implementations do not.

---

## 📚 Practice Exercises

1. **Map and reduce by hand.** Using `sample_data/events.csv`, write a short Python script that implements a naive map phase producing `(region, amount_eur)` pairs and a reduce phase summing by region. Verify it produces the same four rows as `aggregate_events` and `render_summary_csv`.
2. **Inspect the partition model.** Use `partition_for_date`, `partition_for_event`, and `filter_rows_for_partition` to show that every event in `sample_data/events.csv` belongs to partition `20260115`. Then use `sample_data/malformed_events.csv` and explain why partitioning decisions belong after validation.
3. **Prove replay safety.** Run `project.run_pipeline` over `sample_data/events.csv` twice with `idempotent=True`. Compare the `loaded_rows` and `idempotency_keys` across runs and explain what would break if the deduplication key included the load timestamp.
4. **Model Hadoop's operational cost.** Use `cost_model.estimate` to compare a Dataproc cluster with 100 vCPU-hours against a Dataflow job with 100 vCPU-hours and a BigQuery partitioned batch scan of 1 TB. Explain why the right comparison is "work performed", not "cluster size".
5. **Design a JournalNode quorum.** For a 40-node Hadoop cluster, specify the NameNode, NodeManager, and JournalNode layout, including how many replicas and which rack-awareness setting you would use. Describe exactly what happens during an active NameNode failure.
6. **Diagnose a YARN failure.** Write a checklist an on-call engineer would follow for the error `Container killed by YARN for exceeding memory limits`. Include the order in which you would inspect container memory, JVM heap, queue limits, and NodeManager health.
7. **Read the service catalog for Hadoop's successors.** Using `service_catalog.get_service`, print the name, data role, and pricing model for `dataproc`, `dataflow`, `composer`, and `dataform`. Then write two sentences per service explaining whether it replaces HDFS+YARN, MapReduce, or Oozie.
8. **Extend the simulator.** Add a helper to `project/core/pipeline_logic.py` style code (in your own file, without modifying the course modules) that groups accepted events by `channel` as well as `region`, and compare the result against the region-only aggregate.

---

## 📖 Further Reading

- [Apache Hadoop: HDFS Architecture](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)
- [HDFS High Availability Guide](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithJournalNodes.html)
- [Apache Hadoop: YARN Architecture](https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YARN.html)
- [Apache MapReduce Tutorial](https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)
- [Google Cloud Dataproc Documentation](https://cloud.google.com/dataproc/docs)
- [Google Cloud Dataproc: Overview of Hadoop Components](https://cloud.google.com/dataproc/docs/concepts/components-overview)
- [Google Cloud Dataproc Pricing](https://cloud.google.com/dataproc/pricing)
