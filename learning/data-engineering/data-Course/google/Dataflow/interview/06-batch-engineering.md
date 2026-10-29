# Module 6 — Batch Engineering

> **14 questions · Module 6 · Batch Engineering**

---

## Design

### 1. What does "filter early, aggregate early" actually buy you in a Beam batch job?

It buys you a smaller shuffle, and on Dataflow the shuffle is billed and timed. Filtering before a `CombinePerKey` means fewer bytes cross the network and fewer keys are materialised on the workers; aggregating before a shuffle means you carry one accumulator per key instead of one row per event.

The mechanism is Beam's fusion and the runner's choice of where to place a shuffle boundary. When you `Filter` then `KeyByRegion` then `CombinePerKey`, the filter is a pure per-element step that fuses with the parse and often with the read. The `CombinePerKey` then forces a real shuffle. The amount of data crossing that shuffle is what shrinks.

Concrete numbers from a pipeline like `batch_template.py`: 5 million order rows at 300 bytes each is about 1.5 GB read. If 90% of rows are `cancelled` and only 10% count toward revenue, filtering first takes the shuffle from 1.5 GB to 150 MB — a 10× reduction in shuffle bytes, which is a direct reduction in both runtime and cost.

The trade-off: the filter has to be *correct*. Filtering early means you cannot go back and re-include dropped rows without a re-run, and a filter whose predicate is subtly wrong silently under-counts. That is why the course pipeline filters by an explicit `statuses` tuple, and why the test asserts the cancelled order is *excluded* in the default case and *included* when the status list contains it.

### 2. Side input versus shuffle join — how do you choose?

A **side input** broadcasts a small PCollection to every worker and lets you look it up in memory. It is a map join with no shuffle at all, and it is dramatically cheaper when the build side is small. The rule is that the side input must fit in the memory of every worker — typically something under 100 MB of decoded objects, so you size it accordingly.

A **shuffle join** (`CoGroupByKey`, or two `CombinePerKey`s merged with it) moves data across the network and costs a full shuffle, but it scales to either side being large.

The decision rule: if the build side fits comfortably in worker memory *and* is small enough that you can tolerate a few seconds of startup to load it, use a side input. If the build side is larger than a few tens of megabytes, or it changes often enough that re-broadcasting is expensive, use a shuffle join.

The production failure story: a pipeline enriched orders with a currency-rate side input read from GCS. The rates file started at 400 rows and was fine. Two years later it was 40 million rows, the side input became 6 GB, and workers began OOMing — the job failed with `Java heap space` on one worker, retried three times, and failed the whole run. The fix was to move to a `CoGroupByKey` join against a `CombinePerKey`-aggregated rates table. The lesson: side inputs are a size-bounded optimisation, and nothing enforces the bound for you.

### 3. What does Beam actually guarantee about exactly-once, and what does it not?

Beam's model is **at-least-once data processing** with **exactly-once stateful processing for stateful transforms**. In practice that means: the runner can deliver an input element more than once (a worker can fail after processing but before the checkpoint commits), and Beam will not deduplicate your source data for you. But when a transform is stateful — a `CombineFn` accumulator, a `GroupByKey` group, a stateful `DoFn` — Beam's checkpointing ensures the state is rolled back and replayed consistently, so the *output* of the stateful stage is not duplicated.

The gap is at the boundary. If your pipeline ends with `WriteToText` to GCS and the job fails after writing some shards but before the job reports success, a re-run writes *more* shards. `WriteToText` does not deduplicate; GCS has no primary key to deduplicate on. This is why idempotency has to be built into the sink, not hoped for.

The other half is the source. Pub/Sub is explicitly at-least-once, and Beam's `ReadFromPubSub` will redeliver. Batch file sources are typically exactly-once *per file* because the runner tracks which files it has already read, but a re-run from scratch re-reads everything.

So: the honest answer is "exactly-once for state, at-least-once at the edges; make your sink idempotent and you get the illusion your stakeholders want."

### 4. What makes a Beam pipeline deterministic, and why does it matter operationally?

A deterministic pipeline produces the same output for the same input, regardless of how the runner splits the work. That requires: no reliance on iteration order of an unordered collection, no `random` without a fixed seed, no `datetime.now()` inside the pipeline logic (use element timestamps instead), and no side effects outside the pipeline.

The operational payoff is enormous: you can compare the output of a backfill against the original run and *know* that any difference is a data difference, not a scheduling difference. Without determinism, every backfill is an unverifiable gamble.

A subtle way to lose determinism is a `CombineFn` whose `merge_accumulators` is order-dependent — for instance, concatenating a list of values rather than summing them. The course's `RevenueByRegionFn` is deliberately order-independent, and `test_merge_is_order_independent` in `project/tests/test_pipelines.py` proves it by accumulating two disjoint halves in opposite orders and asserting the same output. If merges were order-dependent, a backfill could produce a different revenue total every time you ran it, and nobody would be able to explain why.

### 5. Why should a DLQ be a tagged-output branch rather than a filter that drops rows?

Because a filter that drops rows is *invisible*. If you `Filter` out malformed records and never write them anywhere, the pipeline's output count no longer matches its input count, and the discrepancy has no artefact to inspect. The only symptom is that totals are lower than expected, usually discovered days later by a finance team.

A tagged-output branch writes the rejected elements to a *separate output path*, so every rejected record has a durable home. You can then count DLQ rows, sample them, replay them after fixing the parser, and audit that the DLQ is empty.

In Beam 2.77 the mechanism is `TaggedOutput` — a `DoFn` yields a tagged output to route the element down a second branch:

```python
from apache_beam.pvalue import TaggedOutput


class SplitFn(beam.DoFn):
    GOOD = "good"
    BAD = "bad"

    def process(self, order):
        if order is None:
            yield TaggedOutput(self.BAD, order)
        else:
            yield TaggedOutput(self.GOOD, order)


split = orders | "Parse" >> beam.ParDo(ParseOrderFn()) | "Split" >> beam.ParDo(SplitFn())
good = split[SplitFn.GOOD]
bad = split[SplitFn.BAD]
```

The `bad` branch then gets its own `WriteToText` to a DLQ prefix, and a `bad | "Count" >> beam.combiners.Count.PerKey()` gives you a number to alert on.

The trade-off is cost and complexity: the DLQ branch is another sink, another schema, another thing to monitor, and it must be cleaned up or it will quietly accumulate terabytes. But an unmonitored DLQ is still strictly better than a silent drop, because at least it exists.

The production story: a batch job dropped ~0.3% of rows because a currency code had been added upstream. It took three weeks to find, and the fix required re-running a month of history to recover the lost revenue — which is another 40 hours of compute and a completely separate backfill project.

### 6. What is a poison pill, and how do you stop one?

A **poison pill** is an input element that cannot be processed and takes the pipeline down with it. In Beam, the usual cause is an exception escaping a `DoFn.process`: `raise ValueError` on an unparseable line, a `KeyError` on a missing field, a `TypeError` from a coder mismatch.

Beam's runner treats an unhandled exception in a `DoFn` as a pipeline failure. The worker fails, the runner retries the bundle (and sometimes the whole worker), and if the input is deterministic, the same element fails again. After the retry budget is exhausted, the job fails. A single bad row in a billion-row input can take down a job that had already run for 40 minutes.

The defences, in order of preference:

1. **Make the `DoFn` total** — catch the parse error, log it, and return nothing. The course's `parse_event` does exactly this for streaming; the same discipline applies in batch.
2. **Route failures to a DLQ** so the bad record is preserved rather than lost.
3. **Set a retry budget deliberately** — `--retry_count` and the max attempts — so a flaky source does not kill the job, while understanding that a deterministic poison pill will still fail.

The failure I remember: a nightly job that failed at 03:10 for three consecutive nights because one file in the input bucket contained a UTF-8 BOM that broke the header parser. The job had no DLQ and no partial-output policy, so 40 minutes of compute was wasted every night and nobody got the report. The fix was a `try/except` around the header parse plus a retry-friendly input layout.

### 7. When should you use `GroupByKey` instead of `CombinePerKey`?

Only when you genuinely need the *entire group* in memory at once — for example, to sort the group, to compute an exact percentile from the full set, or to emit all members of the group downstream. `GroupByKey` materialises every value for a key in memory on one worker; `CombinePerKey` keeps a compact accumulator and merges partial results, so memory is bounded by the number of *keys*, not the number of *rows*.

The boundary condition is roughly: if the average group size times the value size exceeds a few hundred MB, `GroupByKey` will not fit. With `CombinePerKey`, a group of a million rows of 100 bytes costs a single scalar accumulator.

The production failure: a pipeline computing "top 10 products per category" used `GroupByKey` and a Python sort. One category had 40 million rows, the worker OOMed, the job failed after 3 hours, and the retry failed identically because the data was the same. The fix was a two-stage approach: `CombinePerKey` to a bounded per-category aggregate, then a much smaller `GroupByKey` over the reduced data. If you truly need a global top-k, the standard trick is to keep a bounded heap in the accumulator — the accumulator stays O(k) regardless of group size.

### 8. What is pre-aggregating before a shuffle, and when does it change the answer?

Pre-aggregating is inserting a `CombinePerKey` *before* the expensive join or shuffle, so you carry one aggregate per key instead of a million rows per key into it. The transformation is valid because aggregation is associative and commutative — sum of sums equals sum.

It changes the answer in exactly one way: if the downstream stage needs per-row detail, pre-aggregation destroys it. If you need "sum of revenue per region per category", you can pre-aggregate on `(region, category)` and still join to a dimension table on `region` — but you can no longer recover the individual order count distribution, or join to an order-level dimension.

The trade-off is also about cardinality: pre-aggregating on a high-cardinality key buys nothing, because the number of distinct keys is the same as the number of rows. The rule is that pre-aggregation helps when the pre-aggregation key is *coarser* than the final output — which is exactly the situation where you are about to join a fact table to a dimension and the fact table is 100× larger than the dimension.

A concrete case: 500 million click rows joined against 200 ad campaigns. Pre-aggregating clicks by `(campaign_id, day)` reduces 500 million rows to perhaps 2 million, and the join and the shuffle both shrink by a factor of 250. The pipeline finishes in 12 minutes instead of failing at the shuffle after 90.

### 9. What are the traps in schema evolution for a batch pipeline?

The traps are all versions of "the schema changed and nobody told the pipeline".

**The `infer_schema` trap.** `beam.io.ReadFromCsv(..., infer_schema=True)` samples the first few rows to guess types and then *casts the entire file* to those types. Add a column whose first 100 rows are null and it infers `STRING`; add a decimal amount that happens to be `"1234"` in the sample and it infers `INT`, then fails on `1234.56` at row 5 million. Worse, the inference is *non-deterministic across files*, so a pipeline that works on Monday's file fails on Tuesday's.

**The silent widening.** A column that was `INT64` becomes `FLOAT64` because a new row has a decimal. BigQuery accepts it, the schema changes, and downstream dashboards that expect `INT64` now break.

**The missing column.** The upstream file gains a column. If the parser is positional (`csv.reader` plus index access), every row shifts and you get plausible-looking wrong numbers instead of an error.

**The dropped column.** The upstream file loses a column and a positional parser raises `IndexError` — which is at least loud.

The defences: pin the schema explicitly rather than inferring it; parse by header name, not position; validate the header at the start of the job and fail with a clear message; and keep the schema version in the output table so a change is visible in the data, not just in the code.

### 10. What should you do when the input schema changes mid-stream of jobs?

Treat it as a versioned contract, not an incident. Concretely, in order:

1. **Detect it explicitly.** Validate the header in the first record and compare it against the expected schema; fail the job with `schema mismatch: expected [a,b,c], got [a,b,d]` rather than parsing garbage. A loud failure at second zero costs one minute; a silent misparse costs a month of wrong numbers.
2. **Version the parser.** Give the parser a version and keep the old one runnable, so a backfill of last month uses last month's parser. This is the difference between a backfill that reproduces the original numbers and one that quietly differs.
3. **Version the output.** Write to a new table or a new column set, and switch consumers over, rather than mutating the table in place.
4. **Backfill with the historical parser** for anything that needs recomputation.

The production story: a partner added a `refund_amount` column as a string, `"0.00"` on most rows and `"12.34"` on some. A `float()` cast accepted both. But an upstream *reordering* of two columns broke a positional parser, and revenue by region came out 8% high because `region` was being read from the `channel` column. Nothing crashed. The pipeline had no header validation, so it went unnoticed for six weeks.

### 11. What does idempotency mean for a batch Beam pipeline, and how do you get it?

Idempotency means re-running the job over the same input produces the same final state, not an additional copy of it. For a `WriteToBigQuery` pipeline, `WRITE_TRUNCATE` on a partition gives you that: the re-run replaces the partition. `WRITE_APPEND` does not — the re-run duplicates every row.

For a GCS output, idempotency comes from writing to a deterministic path and making the re-run replace it, or from writing to a partitioned prefix and deleting the partition before the re-run. `WriteToText` appends a new shard file each time, so `gs://bucket/out/` will contain `out-00000-of-00001` from run 1 and `out-00000-of-00001` from run 2 with different content — the second overwrites the first for the same shard name, but if the shard count differs you get a mix of old and new files. The robust pattern is to write to a run-specific prefix and promote it, or to delete the destination prefix first.

The practical answer for most teams: make the sink's write disposition idempotent and make the pipeline deterministic, then a re-run is always safe. Then the operator's only question is "should I re-run?", and the answer is always yes.

### 12. What is a backfill versus a re-run, and how do you choose?

A **re-run** is the same job over the same input range, usually because the job failed or the code changed but the data did not. A **backfill** is a run over a *historical range* that the pipeline did not originally cover, or over a range whose results need to be recomputed with new logic.

The distinction matters because a backfill usually needs **partition-scoped writes** to avoid clobbering the live data. If your pipeline writes to `orders_summary` with `WRITE_APPEND` and a `run_date` column, a backfill for March appends March rows that are already there — duplicating them. If it writes with `WRITE_TRUNCATE` on the *table*, a backfill deletes April, May and June. You need per-partition truncation: write to `orders_summary$20260301`, truncate that partition, and write the day's data.

The mechanics: give the pipeline an explicit `--start-date` and `--end-date`, derive the partition from the *event* timestamp rather than processing time, and truncate each target partition before writing. Then a backfill is just a re-run with a different date range, and it is safe to run twice.

### 13. What does a backfill actually cost, and how do you make it affordable?

A backfill over 30 days of data costs roughly what 30 days of normal runs cost, plus whatever inefficiency the historical data carries. If the daily batch uses 10 vCPU-hours, a 30-day backfill is 300 vCPU-hours ≈ **$15–30** at $0.05–0.10 per vCPU-hour — before BigQuery read/write costs, which are often larger than the compute.

The levers, in the order they pay off:

1. **Partition the backfill.** Run one job per day (or per week) rather than one job over 30 days. This keeps memory bounded, gives incremental progress, and lets you resume from the failed day instead of restarting.
2. **Right-size the workers.** A backfill over 30× the data does not need 30× the workers, but it does need enough to avoid a single-worker shuffle bottleneck.
3. **Filter aggressively to the date range** so the backfill does not read 30 days to process 1 day.
4. **Use a batch source, not a streaming one.** Streaming mode costs roughly 2–5× batch for the same data because of per-GB and checkpointing overhead.
5. **Watch BigQuery.** A 2 TB scan is billed at roughly $10/TB on-demand. Reading the same partition twice — once to check, once to process — doubles it.

### 14. How do you verify a backfill was correct?

Compare the backfilled result against the original, partition by partition, on three axes: **row counts**, **aggregate values**, and **the set of distinct keys**. Row counts catch "we lost rows"; aggregates catch "we computed the wrong number"; distinct-key counts catch "we collapsed keys" or "we invented a key".

```sql
-- per partition, in BigQuery
SELECT
  DATE(event_date) AS d,
  COUNT(*)              AS backfilled_rows,
  SUM(revenue_eur)      AS backfilled_revenue,
  COUNT(DISTINCT region) AS backfilled_regions
FROM `YOUR_PROJECT_ID.your_dataset.orders_by_region`
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-31'
GROUP BY d;
```

Then diff that against the same query over a snapshot of the pre-backfill table. The tolerance should be zero for a pure re-run of the same code, and *defined* for a backfill with new logic — for instance, if the new code drops `cancelled` orders, the difference should equal the revenue of exactly those orders, which you can compute independently.

Two practical details. First, **snapshot before you overwrite**: copy the affected partitions to a `_pre_backfill` table first, because once the truncate happens the original is gone. Second, **do not trust the job's own success status**. A job can report `JOB_STATE_DONE` and write 40% of the rows if a worker silently produced nothing — which is exactly why the row-count check exists. I have seen a backfill "succeed" that had a per-partition count of 0 for 11 of 30 days, because those partitions had been written by a job that had a stale filter.
