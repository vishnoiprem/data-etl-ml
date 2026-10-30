# Analytics and Cost — Interview Questions

## 🎯 How to use this file

Sixteen questions covering Module 3: BigQuery's execution model, partitioning, clustering, schemas, query optimisation, BigLake, Dataplex and Data Catalog, plus the cost model that turns all of it into money. The cost questions are the ones that separate a candidate who has run a real bill from one who has only read about it — BigQuery bills on bytes scanned, and every optimisation on this list is a way to scan fewer bytes.

## Questions

### Q1. What does BigQuery actually bill you for, and why is it not "per query"?

**Answer.** BigQuery bills for the **bytes scanned** by your query, not for the number of queries. On-demand pricing is $6.25 per TB scanned in `us-central1`. A query that reads 1 MB costs essentially nothing; a query that reads 1 TB costs $6.25.

**Mechanism.** BigQuery is columnar and column-oriented: it stores data in column blocks and skips blocks it does not need, but it still charges for every block it *does* read. The billing unit is bytes of **data scanned**, determined at the column-block granularity, before any filter is applied to the rows within a block.

**Trade-off.** This model is wonderful for exploration — you can query the whole warehouse for free until you start doing it repeatedly — and it is terrible for a dashboard that runs 200 queries an hour over the same data. That is precisely what flat-rate pricing and slot reservations exist to solve.

**In practice.** The number I quote in interviews: a naive `SELECT COUNT(*)` over a 10 TB unpartitioned table costs **$62.50**. The same query against a table partitioned by day with a filter that prunes to one day costs roughly $0.625. The first number is why you partition everything.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import BIGQUERY_ONDEMAND_PER_TB, estimate

print("1 TB scan:", estimate("bigquery", scanned_tb=1.0).total)
print("10 TB scan:", estimate("bigquery", scanned_tb=10.0).total)
print("per-TB price:", BIGQUERY_ONDEMAND_PER_TB)
```

---

### Q2. When should you choose flat-rate (slot) BigQuery over on-demand, and how do you decide?

**Answer.** Choose flat-rate when your query volume is predictable and consistently high enough that idle slots would cost more than the scans you avoid. On-demand wins for bursty, exploratory or low-volume workloads.

**Mechanism.** Flat-rate bills per slot-hour ($0.06 per slot-hour in `us-central1`) and gives you a fixed allocation of virtual CPUs and RAM that queries share. Reservations let you buy that capacity for one or three years at a discount, with committed-use discounts on top. With editions (Standard, Enterprise, Enterprise Plus) you trade cost for features like slot reservations and data governance.

**Trade-off.** Flat-rate converts a variable cost into a fixed one. If your usage is spiky and you pay for peak on-demand, you overpay for the peaks; if you reserve for the average, you queue in the peaks. You need real usage history to make this call — a gut feel is how teams end up with either a $40,000 unused reservation or a $3,000 surprise.

**In practice.** The decision rule I use: look at 90 days of slot usage. If the p95 sustained slot-hours exceed what you would pay for on-demand at that same scan volume, reserve. I also start with the **annual committed-use discount** on on-demand before jumping to flat-rate — it gives a discount with none of the commitment risk.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import BIGQUERY_SLOT_HOUR, estimate

# 1000 slot-hours a month, flat rate.
flat = estimate("bigquery", slot_hours=1000).total
print(f"flat-rate 1000 slot-hours: ${flat:.2f}")

# The same work as on-demand scans.
scan = estimate("bigquery", scanned_tb=20.0).total
print(f"on-demand 20 TB: ${scan:.2f}")
```

---

### Q3. Explain partitioning. What are the rules, and what is "partition pruning"?

**Answer.** Partitioning splits a table by a column value — almost always a date — into separate physical partitions. Query-time pruning is what BigQuery does when it skips partitions that a filter excludes, so the query only reads the bytes it needs.

**Mechanism.** BigQuery supports ingestion-time partitioning (`_PARTITIONDATE`), integer-range partitioning, and — since 2021 — **partitioned tables**, where you choose a `DATE`, `DATETIME`, `TIMESTAMP` or `INT64` column. When a query has a predicate on that column, BigQuery evaluates it against the partition metadata and skips whole partitions without opening them.

**Trade-off.** Partitioning is free to declare and nearly free to maintain, but it has real limits: a table can have up to 10,000 partitions, and each partition has a minimum size, so over-partitioning — say by hour on a low-volume table — creates thousands of tiny partitions that each cost storage and hurt scan performance.

**In practice.** The rules I enforce in code review: partition by a date column, always ingest-time partition as well if the table is append-only, never partition by a high-cardinality column, and check that the partition column is in the clustering set. For the course's pipeline, `partition_for_date("2026-01-15")` returns the decorator `20260115` — the same convention BigQuery uses.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import partition_for_date, partition_for_event

print(partition_for_date("2026-01-15"))
print(partition_for_event("2026-01-15T09:30:00+00:00"))
```

---

### Q4. What is clustering, and how does it differ from partitioning?

**Answer.** Clustering sorts a table's data by up to four columns and stores it so that queries filtering on those columns read fewer bytes. Partitioning splits the table into separate chunks by value; clustering organises the data *within* each partition.

**Mechanism.** BigQuery stores data in **blocks** and **columnar segments**. Without clustering, blocks are laid down in ingestion order, so a filter has to read every block. With clustering, the data is sorted by the clustering columns, so the blocks containing matching values are adjacent and the others can be skipped — the effect is that clustering reduces bytes scanned even without a partition filter.

**Trade-off.** Clustering has no query-time cost, but it does consume storage, and a table with a clustering column that is highly skewed — 90% of rows sharing one value — buys you much less. Clustering also helps most when combined with partitioning; on a small table it does very little.

**In practice.** I cluster on the columns the query filters and groups by that are not the partition column: typically `event_date`, `region`, `event_type`. BigQuery's clustering is automatic and re-applied in the background — there is no job to run — and I recommend re-clustering a table after a bulk load so the layout reflects the new data immediately.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import estimated_scan_bytes

rows = [{"event_id": f"e{i}", "region": "AMER" if i % 4 else "EMEA"} for i in range(4800)]

full = estimated_scan_bytes(rows, partitioned=False)
pruned = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)
print(f"unpartitioned: {full:,} bytes")
print(f"pruned to 1%:  {pruned:,} bytes")
print(f"reduction: {full / max(pruned, 1):.0f}x")
```

---

### Q5. When do you choose a partitioned table over a clustered table?

**Answer.** Partition when you filter by a *range* — a date window, usually. Cluster when you filter by *equality* on a high-cardinality column, or when you need to group by those columns.

**Mechanism.** Partition pruning is a metadata operation: the partition's row range is known, so an entire partition is excluded without reading it. Clustering works at block granularity inside a partition, so it prunes less aggressively but applies to equality and grouping predicates, including joins.

**Trade-off.** Partitioning gives the largest byte reduction when the predicate is a range on the partition column. Clustering is more flexible and more forgiving of a mis-chosen column, but the reduction depends on data distribution. If you partition by `event_date` and cluster by `customer_id`, you get both: the date range excludes whole partitions, and within each partition the customer filter skips blocks.

**In practice.** I use both on the same table — partition by date, cluster by the two or three columns you filter and group by most. The combination is nearly always right for an event table, and the cost is essentially zero.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import estimated_scan_bytes

rows = [{"event_id": f"e{i}"} for i in range(4800)]
scan = estimated_scan_bytes(rows, partitioned=True, partition_prune_ratio=0.01)
print(f"partitioned scan: {scan:,} bytes")
print("at $6.25/TB, that is $%.8f" % (scan / 1024**4 * 6.25))
```

---

### Q6. What is a BigQuery schema, and what happens when the data does not match it?

**Answer.** A schema is the declared structure of a table — column names, types and modes. By default BigQuery enforces it on write, so a bad row is *rejected*, not silently coerced.

**Mechanism.** In strict mode (the default), a load job fails with an error listing the rows that did not conform. The **bad records** feature changes this: instead of failing, BigQuery writes the malformed rows to a separate `*_badRecords` table and loads the rest. You can also relax with `STRICT` vs `LEGACY` and set field-level `NULLABLE` / `REQUIRED` / `REPEATED`.

**Trade-off.** Strict mode surfaces data problems loudly, which is correct for a landing zone but will stop a pipeline. The bad-records feature keeps the pipeline running but silently splits your data across two tables — and if you never monitor the bad-records table, you have a quiet data-quality hole.

**In practice.** I use strict mode on the curated table and the bad-records table on the landing table, then alert on the bad-records row count being non-zero. And I use `NULLABLE` for every field in the landing schema — because the first rule of a landing zone is that you accept what arrives and make the *curated* schema the strict one.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import validate_event, REJECT_UNKNOWN_REGION

row = {"event_id": "e1", "user_id": "u1", "event_ts": "2026-01-15T00:00:00Z",
       "event_type": "order", "region": "ATLANTIS", "channel": "web",
       "currency": "EUR", "amount": 10.0}
print(validate_event(row))
print(REJECT_UNKNOWN_REGION)
```

---

### Q7. What are the four stages of a BigQuery query, and which one do you actually optimise?

**Answer.** The stages are: **scan** (read bytes from storage), **shuffle** (redistribute rows for a join or aggregate), **aggregate/compute** (the actual work), and **write results** (materialise the output). You optimise the scan stage most of the time, because it dominates cost.

**Mechanism.** BigQuery reads columnar blocks, then a **shuffle** stage redistributes rows by the join or grouping key across workers — this is where a skewed join explodes. A **join** on a huge table to a tiny table is handled by a broadcast hash join with no shuffle at all, which is why dimension tables belong in their own table rather than joined inline.

**Trade-off.** You can often reduce shuffle cost by pre-aggregating upstream — but pre-aggregating incorrectly loses the ability to re-slice the data, which is a real cost when requirements change.

**In practice.** The questions I ask of any slow query: how many bytes did it scan, was there a shuffle, was the join key skewed, and could a dimension table have been broadcast instead of shuffled? In the BigQuery console the plan visualisation shows each stage's timing and shuffle bytes, and that is where the answer lives.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_by_window, ingest_events

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)
output = aggregate_by_window(accepted)
print(f"{len(output)} (window, region) rows")
print(output[0])
```

---

### Q8. How do you keep BigQuery costs under control when many teams query the same tables?

**Answer.** Use a project-level budget with alerts, separate chargeback by dataset and service account, cap per-team usage with reservations or by routing teams to their own projects, and make the big scans impossible by giving dashboards a view over a pre-aggregated table.

**Mechanism.** BigQuery budgets and alerts are informational and configurable with thresholds and email/webhook notifications. The billing export to BigQuery gives you per-label and per-service-account cost attribution — and service account identity is the cleanest dimension because it maps to a workload, not a human. Maximum bytes billed is a hard project-level guardrail, and there is also a per-query maximum bytes-billed setting.

**Trade-off.** Guardrails that are too tight get hit by legitimate work and trains people to disable them. Guardrails that are too loose do not prevent the bill. There is no free answer here — you tune against real usage.

**In practice.** Three concrete controls: a project budget with 50% and 90% alerts, a billing export into a separate governance project queried for cost by service account and dataset, and `maximumBytesBilled` on every automated job so a runaway join fails fast instead of costing $400 overnight. The dashboard and the cost dashboard share the same labels, so the chargeback is one join away.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from platform_sim import build_demo_project

project = build_demo_project()
costs = project.estimate_monthly_cost()
for service, cost in sorted(costs.items()):
    print(f"{service:<16} ${cost:>9.4f}")
print(f"{'TOTAL':<16} ${sum(costs.values()):>9.4f}")
```

---

### Q9. What is BigLake, and when is it better than a native BigQuery table?

**Answer.** BigLake lets BigQuery query open table formats — Apache Iceberg, Apache HADOOP, Delta Lake and Apache Parquet — stored in your own Cloud Storage bucket, with managed metadata and optional file-level caching. It is for lakehouse architectures where you want open table formats but do not want to run the metadata maintenance yourself.

**Mechanism.** A native BigQuery table has its own storage managed by BigQuery. A BigLake table points at files you own in GCS, and BigQuery maintains the table metadata (partition specs, clustering, snapshots) for you, so you get BigQuery's query engine without BigQuery owning the bytes.

**Trade-off.** You gain portability — Iceberg files can be read by Spark, Trino, Snowflake — and control over the data lifecycle. You give up some of the native performance and simplicity, and BigLake is in preview in some regions, so availability matters. In the course's catalog, BigLake is generally available in 11 regions and in preview in `southamerica-east1`.

**In practice.** I choose BigLake when there is a genuine requirement to share data with a non-BigQuery consumer, or when the storage format is already standardised by the org. If BigQuery is the only reader, a native table is cheaper and simpler. I would not migrate a working native table to BigLake for aesthetics.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, nearest_region

lake = SERVICES["biglake"]
print(lake.summary)
print(lake.pricing_model)
print("preview in:", lake.availability.preview)
print("nearest to southamerica-east1:", nearest_region("southamerica-east1", "biglake"))
```

---

### Q10. What problem does Dataplex solve, and what is the difference between Dataplex and Data Catalog?

**Answer.** Dataplex is a data management and governance plane: it organises your lake zones, manages metadata and lifecycle, and applies governance at scale. Data Catalog is a unified search and metadata index — it is where you *find* things.

**Mechanism.** Dataplex operates over a lake (a source or a managed lake), with zones — typically `raw`, `staging` and `curated` — and assets within them. It applies aspect types (metadata, lineage, security classifications) to assets and drives lifecycle automation and data quality. Data Catalog indexes entries from BigQuery, Cloud Storage, Bigtable and others, with **tag templates** that define the fields a tag can carry.

**Trade-off.** Overlapping metadata surfaces are a real cost. Dataplex is the governance plane, Data Catalog is the discovery plane, and using both means two places to look and two sets of permissions to manage. BigQuery datasets and GCS buckets are indexed into Data Catalog for free, so many teams can use it alone.

**In practice.** I use Data Catalog for search and tag templates because it is free for BigQuery and Storage assets, and Dataplex when I need real lakehouse governance — automatic lineage across a multi-cloud estate, automated zone-based lifecycle, and a governance model that BigQuery's native controls cannot express.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES

for service_id in ("dataplex", "data-catalog"):
    service = SERVICES[service_id]
    print(f"{service.name}: {service.data_role} — {service.summary}")
    print("   resources:", service.key_resources)
    print("   pricing:", service.pricing_model)
```

---

### Q11. Explain how the course's cost model differs from real GCP billing, and why that matters.

**Answer.** The course model reproduces the *shape* of each pricing model with published `us-central1` list prices; it does not reproduce the invoice. Real billing has tiered egress by destination, regional price variation, sustained-use and committed-use discounts, free-tier quotas per billing account, and a dozen per-service dimensions.

**Mechanism.** Each estimator takes only the parameters relevant to the chosen service, so a reader can see exactly which knob drives which price — `storage_gb`, `retrieval_gb`, `egress_gb`, `scanned_tb`, `vcpu_hours`. The `Estimate` carries the individual `EstimateLine` objects, so the total is always explainable rather than a black box.

**Trade-off.** A simplified model is right for teaching *which decision costs what* and wrong for budgeting. Using it as a budget would be a serious mistake.

**In practice.** I use the model to answer relative questions — "is the partitioned version cheaper than the unpartitioned one?", "does streaming cost more than batch?" — and I use a real cost-estimator or a billing export for absolute numbers. The comparison function answers exactly the question a data engineer asks: does the partitioned, streaming version cost more than the simple batch version?

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import compare_architectures, format_comparison

options = compare_architectures(scanned_tb=1.0, partition_factor=0.01)
print(format_comparison(options))
```

---

### Q12. A team says "BigQuery is too expensive". What questions do you ask before changing anything?

**Answer.** Four questions: how many bytes did the query scan, how many times was the same data scanned, who ran the queries, and what is the storage-versus-scan split. The answer is usually redundant scanning, not BigQuery.

**Mechanism.** The `compare_architectures` function demonstrates the shape of the finding: a 1 TB unpartitioned scan costs $6.25 while the same query partitioned to 1% costs $0.0625 — a 100× reduction from the table layout alone, with no change to the query. The demo project shows the same effect: the monthly cost estimate is dominated by the services that run continuously, not by the queries.

**Trade-off.** The fix is not always "partition everything" — a one-off ad-hoc query over a small table is genuinely cheap. The fix is targeted at the queries that run constantly.

**In practice.** I pull the billing export, join it to `jobs` metadata, and rank by total bytes billed. Usually the top three queries are a dashboard, a nightly aggregation, and a `SELECT COUNT(*)` someone left in a view. Then I partition the underlying tables, materialise the dashboard on a view over a scheduled table, and add `maximumBytesBilled` so the next regression fails instead of billing.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

queries = [("dashboard", 40, 8), ("nightly agg", 2, 1), ("ad-hoc count", 0.5, 12)]
for name, tb, runs in queries:
    total = estimate("bigquery", scanned_tb=tb * runs, apply_free_tier=False).total
    print(f"{name:<14} {tb} TB x {runs} runs = ${total:,.2f}")
```

---

### Q13. What is the cost of moving data, and how does it change the architecture?

**Answer.** Network egress from GCP to the internet is $0.12/GB in `us-central1`. That is more than six times the cost of storing the same data in Standard storage for a month ($0.020/GB-month). Moving data *into* GCP is free.

**Mechanism.** Egress is charged per GB by destination tier — internet egress is the expensive case; egress between Google services and between regions is priced differently and is often free or much cheaper. The bill arrives as a separate line item from the service that stored the data, which is why teams discover it late.

**Trade-off.** Keeping data in GCS and querying it with BigQuery avoids egress entirely because the read path is a Google-internal network path. Copying the same data out to a local laptop, or into a competitor's warehouse, is priced as internet egress.

**In practice.** I check egress before I design the copy. A 5 TB backup to another region is cheap or free depending on the path; a 5 TB export to a client S3 bucket is $614. That single number changes whether the deliverable is "a BigQuery dataset" or "a downloadable export", and it changes how often you can repeat it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import NETWORK_EGRESS_PER_GB, estimate

print("egress price per GB:", NETWORK_EGRESS_PER_GB)
result = estimate("cloud-storage", storage_gb=5_000, egress_gb=5_000, monthly=True)
print(result)
```

---

### Q14. How do you make a BigQuery pipeline cost-aware by default rather than by review?

**Answer.** Put the cost control in the deployment: partition and cluster every table from the template, set `maximumBytesBilled` on every automated job, require a `LIMIT` or a partition filter in the CI query checks, and route recurring queries to a materialised view or a scheduled table.

**Mechanism.** BigQuery has no guardrail that requires you to partition — the default is an unpartitioned table, and the expensive query is the one nobody thought about. So the control has to be in the infrastructure-as-code layer, not in a wiki. Materialised views are incrementally maintained: BigQuery refreshes them as the base table changes, so a dashboard reads the small result rather than re-scanning the large table.

**Trade-off.** Materialised views cost storage and a maintenance fee, and they can go stale relative to the base table within the refresh window. Over-partitioning creates tiny partitions. Every guardrail has a cost, and the point of putting it in the template is that you tune it once.

**In practice.** In my template, a new table gets: partitioning by the date column, clustering by the top three filter columns, `require_partition_filter` enabled on the dataset, and a `maximumBytesBilled` on every job template. The course's `estimated_scan_bytes` function models the effect directly — the same query is 100× cheaper against the partitioned layout.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import ingest_events, estimated_scan_bytes

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines)

full = estimated_scan_bytes(accepted, partitioned=False)
pruned = estimated_scan_bytes(accepted, partitioned=True, partition_prune_ratio=0.01)
print(f"full scan:     {full:>12,} bytes")
print(f"partitioned:   {pruned:>12,} bytes")
print(f"cost at $6.25/TB: full=${full/1024**4*6.25:.8f}  pruned=${pruned/1024**4*6.25:.8f}")
```

---

### Q15. A data warehouse table grows to 40 TB. What is your plan?

**Answer.** Find out whether it is one table or many, and whether the growth is append or update. Then: partition it by date, archive cold partitions to cheaper storage, build a summary table for the access pattern that dominates, and only then consider splitting the table.

**Mechanism.** BigQuery's columnar storage compresses repeated values well, so the *scanned* bytes for a narrow query are far smaller than the *stored* bytes. The cost driver is storage per GB-month plus whatever the queries scan. A 40 TB table with 50 columns where queries touch 3 costs nothing extra to scan — but it does cost $800/month to store at $0.020/GB-month.

**Trade-off.** Table expiration and partition expiration trade queryability for cost: you cannot query an expired partition without restoring it. Splitting a table into daily tables makes the "one table" query pattern awkward and forces a wildcard or a union across many tables.

**In practice.** I first measure the *query* pattern from the billing export, then optimise for it: partition by date, cluster by the grouping columns, build a summary table for the dashboard, and set partition expiration to match the actual retention requirement. I almost never split a table manually — partition expiration handles it — unless there is a schema divergence.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

storage = estimate("bigquery", storage_gb=40_000, monthly=True)
print("40 TB stored for a month:", storage)
```

---

### Q16. How would you explain the difference between a "data warehouse" and "BigQuery" to a stakeholder?

**Answer.** A data warehouse is a *pattern* — a subject-oriented, integrated, non-volatile store queried analytically. BigQuery is one *implementation* of that pattern on GCP, and there are others (BigLake over Iceberg, Snowflake, Databricks, Redshift).

**Mechanism.** The classic Inmon characteristics map onto BigQuery as: subject-oriented → datasets per business domain; integrated → shared dimensions and a conformed event schema; non-volatile → BigQuery tables are append-mostly, and you correct rather than overwrite; time-variant → every partition has a timestamp.

**Trade-off.** The pattern is durable, the implementation is not. If you hard-code BigQuery-specific syntax, a future migration to an open-table-format lakehouse (Iceberg on GCS via BigLake) becomes a rewrite of your transformation layer. If you write portable SQL in Dataform, it becomes a configuration change.

**In practice.** I use BigQuery-specific features freely — `QUALIFY`, `SELECT AS STRUCT`, array functions — but I keep the *transformation layer* in Dataform with standard SQL, so the models compile to more than one target if we ever need them to. And I tell the stakeholder the honest thing: BigQuery is not the warehouse, it is this warehouse's current implementation, and we designed so it can change.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from service_catalog import SERVICES, data_role_index

warehouse = data_role_index()["warehouse"]
print("warehouse-role services:", warehouse)
for service_id in warehouse:
    print(f"  {SERVICES[service_id].name}: {SERVICES[service_id].summary}")
```

---

## 📚 Related chapters

- [3.1 — Data Warehousing Concepts](../chapters/12-data-warehousing-concepts.md)
- [3.2 — BigQuery Platform Overview](../chapters/13-bigquery-platform-overview.md)
- [3.3 — BigQuery Query Optimization](../chapters/14-bigquery-query-optimization.md)
- [3.4 — BigLake, Dataplex & Data Catalog](../chapters/15-biglake-dataplex-and-data-catalog.md)

## 📖 Further Reading

- [BigQuery documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery pricing](https://cloud.google.com/bigquery/pricing)
- [Using partitioned tables](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [Using clustered tables](https://cloud.google.com/bigquery/docs/clustered-tables)
- [BigQuery best practices for cost control](https://cloud.google.com/bigquery/docs/best-practices-cost-control)
