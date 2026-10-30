# Streaming and Ingestion — Interview Questions

## 🎯 How to use this file

Fourteen questions covering Module 4: Kafka and the streaming model, Pub/Sub, Datastream and CDC, transfer services, and delivery semantics. The through-line of this module is that **delivery semantics are a design decision, not a property of the tool**. Pub/Sub gives at-least-once delivery and you must make your sink idempotent; Kafka gives ordering within a partition and you must choose the key. Say your answer out loud, then check it.

## Questions

### Q1. What delivery guarantee does Pub/Sub actually provide, and what does that force you to build?

**Answer.** Pub/Sub provides **at-least-once delivery**. A message may be delivered more than once, and a subscriber that crashes mid-processing will have its message redelivered. That forces you to make your sink idempotent — you cannot assume exactly-once.

**Mechanism.** When a subscriber acknowledges a message, the ack is recorded against the message's delivery attempt. If the subscriber dies before the ack lands, Pub/Sub redelivers after the ack deadline expires. The **message retention period** (default 7 days) bounds how long you can wait — if you fall behind longer than that, the message is dropped.

**Trade-off.** At-least-once is the right default: it is impossible to guarantee exactly-once across a network boundary, and pretending otherwise gets you duplicate rows. The cost is that your consumer must be idempotent, which means a deduplication key and a deterministic write.

**In practice.** Every pipeline I build on Pub/Sub has an idempotency key derived from the *data*, never from arrival time. The course's `dedup_key(event_id, partition)` returns `"20260115:evt-0001"` — deterministic, so a retry produces the same identity rather than a new one. That is what makes the retry safe.

**Failure story.** A consumer wrote straight to BigQuery with a streaming insert and no dedup. A transient network fault caused redelivery of a 20-minute batch, and the revenue table gained roughly 4% duplicate rows. The dashboards still looked plausible, which is the worst part. The fix was a deterministic key and a `MERGE` instead of an append.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, deduplicate

rows = [{"event_id": "e1"}, {"event_id": "e2"}, {"event_id": "e1"}]
print("key:", dedup_key("e1", "20260115"))
print("before:", len(rows), "after:", len(deduplicate(rows, partition="20260115")))
```

---

### Q2. What is a Pub/Sub subscription's ack deadline, and why do you need a dead-letter topic?

**Answer.** The ack deadline is how long Pub/Sub waits for your subscriber to acknowledge a message before redelivering it — 10 seconds by default, extendable to 600. A **dead-letter topic** is where messages go when a subscriber explicitly rejects them or when they exceed the maximum delivery attempts.

**Mechanism.** You send a `modifyAckDeadline` request to extend the deadline for a long-running message — this is how you handle a slow downstream without causing redelivery. When you `nack` a message, Pub/Sub redelivers it immediately and increments the delivery attempt count. After the configured maximum attempts, the message is forwarded to the dead-letter topic.

**Trade-off.** A short ack deadline causes duplicate processing when your work takes longer than the deadline. A long one means a crashed subscriber's messages sit undelivered for longer before recovery. Dead-lettering keeps the pipeline running but creates a second queue you must monitor — an unmonitored dead-letter topic is where data quietly disappears.

**In practice.** I set the ack deadline to comfortably exceed the p99 processing time, extend it explicitly for genuinely slow messages, and put a metric on the dead-letter topic's oldest-unacked message age. The alert fires on *age*, not on count — 100 dead letters that arrived a minute ago is nothing, 1 dead letter that arrived three hours ago is an outage.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

print(SERVICES["pubsub"].key_resources)
print(SERVICES["pubsub"].pricing_model)
```

---

### Q3. What are the ordering guarantees in Pub/Sub, and how do you get them?

**Answer.** Pub/Sub does **not** guarantee ordering by default. If you enable message ordering on a subscription, messages with the same **ordering key** are delivered in order — but only within a single region, and the ordered delivery comes at a throughput cost.

**Mechanism.** Ordering is achieved by grouping messages into ordered "delivery batches" keyed by the ordering key, and Pub/Sub will not deliver the next message for a key until the current one is acknowledged. This constrains parallelism: the number of concurrently active ordering keys caps your throughput.

**Trade-off.** Ordering is a real cost in both throughput and complexity — you must design your key so that all messages that must be ordered share it, and you must handle the case where a single hot key becomes the bottleneck.

**In practice.** I only enable ordering where the business logic demands it (a state machine, a sequence with a dependency) and I pick the ordering key deliberately. For the course's pipeline, the natural ordering key is the `event_id` or the `user_id` if per-user ordering matters — and I would use `region` only if I accepted that all events in a region serialise.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import publish_topic

rows = [{"event_id": "e1", "event_type": "order", "region": "AMER"}]
for message in publish_topic(rows, topic="events-normalised"):
    print("topic:", message["topic"])
    print("attributes:", message["attributes"])
    print("body keys:", sorted(message["data"])[:5], "...")
```

---

### Q4. When would you choose Kafka over Pub/Sub?

**Answer.** Choose Kafka when you need **high throughput with per-partition ordering that you control**, long-term retention with replay, or an existing Kafka ecosystem. Choose Pub/Sub when you want a fully managed, low-operations service that scales to zero subscribers.

**Mechanism.** Kafka is a log: topics are split into partitions, each partition is an ordered append-only log, and consumer groups track their offset. Ordering is a property of the partition — messages within a partition are ordered, and the partition is chosen by the key's hash. Retention is a log-segment property, so you can retain days or years and replay from any offset.

**Trade-off.** Kafka gives you control (partitioning, retention, consumer groups, exactly-once with the transactions API) at the cost of operating the infrastructure — brokers, partitions, rebalancing, and the capacity planning that comes with it. Pub/Sub gives you none of that control and none of that cost.

**In practice.** I reach for Kafka when the platform team already runs it and there are multiple consumer teams that need independent replay from different offsets — a log you cannot replay is a pipeline you cannot rebuild. I reach for Pub/Sub for everything else, especially when the consumer count is unpredictable or zero most of the time, because Pub/Sub has no idle cost.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("pubsub", "kafka"):
    service = SERVICES[service_id]
    print(f"{service.name}: {service.summary}")
    print(f"   resources: {service.key_resources}")
    print(f"   regions: {len(service.availability.available)}")
```

---

### Q5. Explain Kafka's consumer group and offset model, and why a rebalance is a scariest moment in a streaming pipeline.

**Answer.** A consumer group is a set of consumers that share the partitions of a topic — each partition goes to exactly one consumer in the group. Each consumer tracks its **offset** — its position in the partition — and the group coordinates assignment via the group coordinator.

**Mechanism.** When a consumer joins, leaves, or fails its heartbeats, the group coordinator triggers a **rebalance**, during which partitions are redistributed. During a rebalance, consumption pauses. The consumer group protocol (the group coordinator, heartbeat-based liveness, the generation protocol) is what stops two consumers processing the same partition.

**Trade-off.** More consumers than partitions means idle consumers — a real ceiling on parallelism. A long rebalance pauses consumption, and a rebalance storm (consumers flapping) turns a pipeline into a stalling one.

**In practice.** I size the consumer group to the partition count, set `max.poll.interval.ms` above the worst-case processing time or the consumer will be kicked for being slow, and use static membership where the client supports it to avoid rebalances on every deploy. I also alert on consumer lag per partition — lag is the number that tells you whether the pipeline is keeping up.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import PUBSUB_PER_GB_INGEST, estimate

print("Pub/Sub ingest price per GB:", PUBSUB_PER_GB_INGEST)
print(estimate("pubsub", pubsub_gb=100, monthly=True))
```

---

### Q6. What is Datastream, and when do you reach for CDC instead of event streaming?

**Answer.** Datastream is a change data capture service: it reads the write-ahead log or binlog of a source database and publishes row changes to a destination, without you writing a CDC pipeline.

**Mechanism.** For Cloud SQL, Datastream uses the database's binlog for MySQL and the logical replication stream for PostgreSQL; for Oracle it uses the redo log. It can read from BigQuery, Cloud SQL, AlloyDB and many SaaS sources (Salesforce, ServiceNow, Workday). Destinations include BigQuery, Cloud Storage, Bigtable and Pub/Sub.

**Trade-off.** CDC captures *state changes* — so it gives you the after-image of every update, including updates to rows you never needed to know changed. Event streaming captures *intent* — a click happened, an order was placed — which is usually smaller and more meaningful. CDC also adds a dependency on the source's log retention: if you fall behind past the log's lifetime, you have a gap.

**In practice.** I use CDC for keeping an operational store and a warehouse in sync, and for capturing changes to a source system where no events exist. I use event streaming for anything where the producer can be changed to emit an event, because a `DELETE` in a log is genuinely harder to interpret than a `deleted` event with a reason.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import DATASTREAM_PER_CDC_ROW, estimate

print("per CDC row:", DATASTREAM_PER_CDC_ROW)
print(estimate("datastream", rows=1_000_000, stream_hours=24, monthly=True))
```

---

### Q7. How do you handle schema changes in a CDC or streaming pipeline?

**Answer.** Use a schema registry with an enforced compatibility mode — typically `BACKWARD` or `FULL` for Avro — so a producer cannot publish a breaking schema. In the sink, keep the raw payload alongside the parsed fields so a schema change does not require re-reading history.

**Mechanism.** Schema compatibility modes define what changes are allowed: `BACKWARD` means a new consumer can read data written by the old schema, `FORWARD` means an old consumer can read new data, `FULL` means both. A `FULL`-compatible change adds a field with a default; removing a field or changing its type is not `FULL`-compatible.

**Trade-off.** Strict compatibility blocks legitimate changes — you cannot rename a field at all. Loose compatibility lets the schema drift and pushes the burden onto every consumer, which is how a "flexible" schema becomes a mess of optional fields nobody can rely on.

**In practice.** I run `BACKWARD` for the shared event schema and treat the registry as a contract with an owner. I also keep a version column in the warehouse so a consumer can tell which schema version produced a row. And critically, I never let the pipeline drop unknown fields silently — the raw payload column is the escape hatch.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

print(SERVICES["pubsub"].key_resources)   # includes "Schema"
print(SERVICES["datastream"].key_resources)
```

---

### Q8. When would you use the BigQuery Data Transfer Service, and what is it actually automating?

**Answer.** It automates the *scheduled load* from a source into BigQuery — Google Ads, Google Analytics, Facebook Ads, Shopify, Salesforce, Teradata, and Cloud Storage. You define a transfer config with a schedule and BigQuery runs the load for you.

**Mechanism.** Each transfer type has a connector that knows how to pull from that source and land it as a BigQuery table, handling incremental loads and schema evolution with its own semantics. You can schedule it on a recurring cadence and inspect each **transfer run** for its status and logs.

**Trade-off.** It removes the cron-plus-script, but it hands you a black-box connector with its own ideas about incremental logic and error handling. If you need custom transformation on load, you are writing a query anyway — and then you might as well control the schedule.

**In practice.** I use it for the sources where the incremental logic is genuinely tedious and standard — ad platforms and SaaS exports — and I write a Dataform or Composer-managed load for anything where I need to control the semantics. The free part matters too: the transfer service itself is free and you pay only the BigQuery query and storage.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["bigquery-transfer"]
print(service.summary)
print(service.pricing_model)
print(service.key_resources)
```

---

### Q9. When would you use the Storage Transfer Service, and how is it different from `gsutil cp`?

**Answer.** Use Storage Transfer Service for large, scheduled, or one-off bulk transfers between Cloud Storage buckets, from cloud providers, or from on-premises storage. `gsutil cp` is a command-line copy — great for a few files, wrong for petabytes.

**Mechanism.** STS creates a **transfer job** that runs a fleet of **agents** which pull data in parallel, with built-in retries, checksum verification, and scheduled transfers. It supports transfers between buckets, from AWS/Azure/other clouds via the interoperability APIs, and from on-prem NFS/SMB over a VPC peering with a custom agent.

**Trade-off.** `gsutil` is one process, one stream, and you babysit it. STS parallelises and is engineered for the failure cases — a dropped connection resumes rather than restarts. STS also introduces a job lifecycle to manage, and for a handful of files it is overkill.

**In practice.** Rule of thumb: if the transfer is more than a few hundred GB, or needs to run repeatedly, or has to survive your laptop closing, use STS. The economics follow the same shape as egress — a 10 TB transfer *into* GCS is free, and a 10 TB transfer *out* to the internet costs $1,228.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import NETWORK_EGRESS_PER_GB, estimate

result = estimate("cloud-storage", storage_gb=10_000, egress_gb=10_000, monthly=True)
print(result)
print(f"10 TB out at ${NETWORK_EGRESS_PER_GB}/GB")
```

---

### Q10. What is the Database Migration Service, and how does it get a database to GCP with low downtime?

**Answer.** DMS is a self-service, low-downtime path to move an existing database into Cloud SQL. It handles the schema migration, the bulk data copy, and the cutover.

**Mechanism.** A **connection profile** describes the source and destination. A **migration job** performs a schema conversion (via a profile that defines the target schema), copies the data in bulk, and then at cutover it stops writes to the source briefly, applies the remaining changes, and points the application at the new instance. The write-stop is typically seconds to a minute.

**Trade-off.** The migration itself is billed per connection-hour, but the real cost is the *cutover risk*: you need a tested rollback, and you need to have verified that the schema, the extensions and the semantics all match.

**In practice.** I do a rehearsal on a restored copy first, and I run the cutover with a written runbook that names the exact rollback command and the decision time to abandon. I also check the hard parts in advance: sequences, triggers, foreign keys, timezone behaviour and collation — those are where "the same schema" quietly stops being true.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

service = SERVICES["database-migration"]
print(service.summary)
print(service.pricing_model)
print(service.key_resources)
```

---

### Q11. How do you design a streaming ingest path so that a consumer restart does not lose or duplicate data?

**Answer.** Acknowledge only after the downstream write succeeds, make the write idempotent with a deterministic key, and use a dead-letter topic for messages that cannot be processed.

**Mechanism.** The redelivery contract is the whole design. Because Pub/Sub redelivers on crash, the sequence "write then ack" gives at-least-once, and the idempotency key turns at-least-once into effectively-once at the sink. The course's pipeline makes the key deterministic: `dedup_key(event_id, partition)` produces `"<partition>:<event_id>"`, and `deduplicate()` removes repeats while preserving order.

**Trade-off.** Exactly-once is not achievable across Pub/Sub and BigQuery without a transactional sink, so the honest claim is "at-least-once delivery, idempotent processing, effectively-once result". Writing that in the design doc is what stops the "but is it exactly-once?" question in a review.

**In practice.** Three rules, always: ack after the write, never derive identity from arrival time, and make the sink's write a `MERGE` on the deterministic key rather than an append. The reason the third rule matters is that even with dedup in the pipeline, a replay from the dead-letter path can deliver a message you already loaded.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, dedup_key_set, deduplicate

rows = [{"event_id": "e1"}, {"event_id": "e2"}, {"event_id": "e1"}, {"event_id": "e3"}]
keys = dedup_key_set(rows, "20260115")
print("distinct keys:", sorted(keys))
print("deduped rows:", len(deduplicate(rows, partition="20260115")))
```

---

### Q12. What is the difference between processing time and event time, and why does it matter?

**Answer.** Processing time is when your system handles the event; event time is when the event actually happened. Windowing on the wrong one produces answers that look right and are wrong.

**Mechanism.** The course's `bucket_by_window` derives the window from the **event timestamp**, never from arrival time. The comment in the code says it plainly: skip the re-stamping step and every event collapses into a single window — the totals stay right, which is exactly why the bug is easy to miss. The dataset spans 24 hours and produces exactly 24 hourly windows.

**Trade-off.** Event-time windowing is correct but requires handling **late data** — events that arrive after their window has closed. Processing-time windowing avoids that problem and produces results nobody can reconcile with the source data.

**In practice.** I use event time, with a **watermark** that declares how late is late enough. In Beam, a watermark is the system's claim about completeness; the course's `watermark_lag` measures the gap between the watermark and the newest event, which is the number that tells you whether the pipeline is keeping up. Events later than the watermark go to a side output for reprocessing.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import bucket_by_window, hours_spanned, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

windows = bucket_by_window(accepted)
print("hourly windows:", len(windows))
print("hours spanned:", hours_spanned(accepted))
```

---

### Q13. What does it cost to run a streaming pipeline, and why do "idle" pipelines cost money?

**Answer.** A Dataflow streaming job bills per worker-hour for as long as it runs, whether or not it is processing data. An idle streaming pipeline is a full-billing idle pipeline.

**Mechanism.** The price is $0.0595 per vCPU-hour for Dataflow streaming, and $0.0476 per vCPU-hour for Dataproc. The billing is on provisioned capacity, not on throughput. The course's `compare_architectures` makes the point directly: with `streaming_hours=0` the Dataflow line is $0.00, and the cost only appears once you set the hours.

**Trade-off.** Always-on streaming gives low latency and automatic recovery, and it bills for the whole time. Batch costs only when it runs but has a minimum latency of the schedule interval.

**In practice.** The course's comparison table shows the ordering clearly at 1 TB scanned: unpartitioned batch $6.25, partitioned batch $0.0625, and streaming costs only once you give it hours. The real question is not "batch or streaming" but "how much idle time does streaming pay for". I set a scaling window, and I use streaming only where the latency requirement genuinely needs it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import DATAFLOW_PER_VCPU_HOUR, DATAPROC_PER_VCPU_HOUR

print(f"Dataflow streaming: ${DATAFLOW_PER_VCPU_HOUR}/vCPU-hour")
print(f"Dataproc:          ${DATAPROC_PER_VCPU_HOUR}/vCPU-hour")
print(f"24h x 4 vCPU Dataflow: ${DATAFLOW_PER_VCPU_HOUR * 24 * 4:.2f}")
```

---

### Q14. Your ingest pipeline is falling behind. Walk me through the diagnosis.

**Answer.** Find the constraint first: is it the source, the broker, the consumer, or the sink? The metrics to pull are consumer lag, backlog age, per-stage throughput, and sink write latency.

**Mechanism.** Lag is the gap between what has been produced and what has been consumed. If lag grows linearly while throughput is flat, the consumer is the constraint. If throughput drops but the consumer has headroom, the source or the broker is. The age of the oldest unprocessed message is the number you put in front of a stakeholder — "12 minutes behind" is meaningful, "120,000 messages" is not.

**Trade-off.** The instinct is to add consumers, but adding consumers to a Kafka topic does nothing if you have not increased the partition count, and it adds rebalance overhead. The instinct is also to raise the ack deadline, but that only postpones the redelivery, it does not fix throughput.

**In practice.** I check, in order: consumer lag per partition (is it one partition hot?), sink write latency (is BigQuery the bottleneck?), CPU and GC on the workers, and the retry rate. Then I fix the specific stage. The most common finding is a hot partition — one key with far more traffic — and the fix is a better key or more partitions, not more workers.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import watermark_lag, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

print("watermark lag:", watermark_lag(accepted))
print("oldest event:", accepted[0]["event_dt"])
print("newest event:", accepted[-1]["event_dt"])
```

---

## 📚 Related chapters

- [4.1 — Kafka & the Streaming Model](../chapters/16-kafka-and-the-streaming-model.md)
- [4.2 — Pub/Sub](../chapters/17-pubsub.md)
- [4.3 — Datastream & CDC](../chapters/18-datastream-and-cdc.md)
- [4.4 — Transfer Services & Migration](../chapters/19-transfer-services-and-migration.md)

## 📖 Further Reading

- [Pub/Sub documentation](https://cloud.google.com/pubsub/docs)
- [Pub/Sub exactly-once delivery](https://cloud.google.com/pubsub/docs/exactly-once-delivery)
- [Pub/Sub dead-letter topics](https://cloud.google.com/pubsub/docs/dead-letter-topics)
- [Datastream documentation](https://cloud.google.com/datastream/docs)
- [Storage Transfer Service documentation](https://cloud.google.com/storage-transfer/docs)
