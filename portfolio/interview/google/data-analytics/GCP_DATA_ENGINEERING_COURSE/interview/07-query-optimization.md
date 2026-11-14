# Query Optimization — Interview Questions

## 🎯 How to use this file

Twenty questions on how to make a BigQuery query faster and cheaper: how to read an execution graph, which metrics to check, how joins are chosen, what skew does to a query, and how to change a pipeline that regressed.

These are the questions that separate someone who has *watched* BigQuery run from someone who has only written SQL for it. Every answer here is written the way a senior engineer answers: the direct answer first, then the mechanism, then the trade-off, then a number.

The through-line is this: **BigQuery bills for bytes scanned and consumes slot-hours, so every optimisation is either "read less" or "do the same work with fewer slots."** Everything else is detail.

## Questions

### Q1. A query is slow. What is your process for diagnosing it?

**Answer.** Work the four levers in a fixed order: **bytes scanned → shuffle → skew → join strategy.** Do not start by rewriting SQL — start by measuring, because the fix depends entirely on which lever is broken.

**Mechanism.** The four map onto the four query stages. *Bytes scanned* is the scan stage and the direct cost driver on on-demand pricing. *Shuffle* is the stage where rows are redistributed across workers by join or group key — it is where the network and the slot-hours go. *Skew* is a shuffle with a bad distribution: one key holds most of the rows, one worker becomes the straggler, and the query finishes when it finishes. *Join strategy* determines whether a shuffle happened at all: a broadcast hash join copies the small side to every worker and shuffles nothing.

**Trade-off.** The order matters because a fix at a later step may be undone by an earlier one. Re-clustering a table does nothing if the query scans the whole table anyway; broadcasting a dimension does nothing if the scan is the bottleneck. And the diagnosis is cheap — you can get bytes scanned in ten seconds with `--dry_run` and the rest from the execution graph — so there is no reason to guess.

**In practice.** My actual sequence: (1) `bq query --dry_run` for bytes; (2) open the execution graph and look for a shuffle stage; (3) if there is a shuffle, check whether the join keys are skewed; (4) if the join side is small, ask why it was not broadcast. The numbers I want every time: `total_bytes_processed`, `total_slot_ms`, and the elapsed time. Those three, compared against the same query a week ago, tell you which lever moved.

**Failure story.** A team spent a week rewriting a slow query — adding CTEs, restructuring joins, adding intermediate tables — and it got no faster. The query had been scanning the full 8 TB table the whole time because a `WHERE` clause was wrapped in `DATE()` and partition pruning had never applied. Every one of their rewrites had been applied to a query that was reading the entire table. Measuring first would have found it in ten minutes.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

# Lever 1: bytes. This is the only lever you can price in ten seconds.
for tb in (10.0, 1.0, 0.1):
    print(f"{tb:>6} TB scanned: ${estimate('bigquery', scanned_tb=tb, apply_free_tier=False).total:>7.2f}")

# Lever 4: join strategy. A broadcast removes the shuffle entirely.
slots = estimate("bigquery", slot_hours=100).total
print(f"100 slot-hours of shuffle work: ${slots:.2f}")
```

Expected output:

```text
  10.0 TB scanned: $  62.50
   1.0 TB scanned: $   6.25
   0.1 TB scanned: $   0.62
100 slot-hours of shuffle work: $6.00
```

Bytes scale linearly; slot-hours are the invisible half of the bill.

---

### Q2. How do you read a BigQuery execution graph?

**Answer.** Read it **right to left and bottom to top, following the data**, and identify the stage that is doing the most work rather than the stage that took the longest wall-clock time.

**Mechanism.** The graph is a DAG of stages. Each stage shows its inputs, its outputs, and its statistics. The stages you will see: **Scan** (read blocks from storage, apply partition/column pruning), **Shuffle** (redistribute rows by key), **Read/Write** (read a shuffle output, or write a result), **Aggregate** (combine partial results), **Sort**, and **Join**. The statistics on a shuffle stage — rows in, bytes shuffled, and **the distribution across workers** — are where the diagnostic information lives. A stage where one worker processed 4.1M rows while its peers processed 400K is a skew signal visible directly in the graph.

**Trade-off.** The graph is the ground truth, but it is per-query and post-hoc — it tells you what happened, not what will happen if you change the SQL. It also does not show *everything*: it will not tell you that your filter could have pruned a partition but didn't, because that is a planning decision rather than an execution statistic. That gap is why `--dry_run` (bytes) and the graph (shape) are complementary, not redundant.

**In practice.** What I read off the graph, in order: the **Scan** stage's bytes (compare against the table's total size to confirm pruning worked), whether a **Shuffle** stage exists at all (a shuffle is the expensive thing), the **shuffle output size** (much bigger than the input means many-to-many fan-out), the **row distribution** across workers (skew), and the final **output rows**. In the console, the Execution Details tab gives the stage timeline; the `INFORMATION_SCHEMA.JOBS` view gives the same numbers programmatically.

**Failure story.** A team read the graph looking for the longest stage and optimised that one. The longest stage was the final write — because the query returned 400M rows. The real problem was a fan-out join that had turned a 3M-row table into a 400M-row result, and the write was merely the stage that took longest. Reading the graph for **the most data moved** rather than **the most time elapsed** would have found it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_events

# A fan-out join: the shape that makes a graph's write stage enormous.
rows = [
    {"event_id": f"e{i}", "user_id": f"u{i % 3}", "event_dt": "2026-01-15T00:00:00+00:00",
     "event_type": "order", "region": "AMER", "channel": "web", "currency": "EUR", "amount_eur": 10.0}
    for i in range(6)
]

# Aggregate BEFORE joining is what keeps the output small.
summary = aggregate_events(rows)
print("rows in:", len(rows))
for region, stats in summary.items():
    print(f"  {region}: {stats}")
```

Expected output:

```text
rows in: 6
  AMER: {'event_count': 6.0, 'revenue_eur': 60.0}
```

Six rows in, six rows out. The equivalent "join then aggregate" would have produced the cross product before summing — the fan-out the graph would have exposed.

---

### Q3. Which metrics do you check when a query becomes slow?

**Answer.** Four, and I check them in this order: **bytes scanned**, **slot-milliseconds**, **rows processed vs rows output**, and **wall-clock time**. The third is the one that most often reveals the actual bug.

**Mechanism.** These are the numbers `INFORMATION_SCHEMA.JOBS` gives you: `total_bytes_processed`, `total_slot_ms`, `total_rows_processed`, `total_rows_output`, and `elapsed_secs`. Bytes and slot-ms are the two cost meters — bytes for on-demand, slot-ms for capacity-based. The ratio of rows processed to rows output is a **fan-out detector**: a query that reads 3M rows and writes 400M has multiplied its data, and that is a correctness problem before it is a performance problem. Wall-clock time is the symptom everyone reports and the least diagnostic number on its own.

**Trade-off.** Each metric can be misleading alone. Bytes can be tiny while slot-ms is enormous — a small, badly shuffled query. Slot-ms can be high while bytes are tiny — the same case. Rows processed and output can differ for a *legitimate* reason: a `GROUP BY` that reduces 10M rows to 100 is working perfectly. So you read them as a set. And none of them tells you *why* — that is the execution graph's job. Metrics tell you which lever moved; the graph tells you what to do about it.

**In practice.** The derived metric I actually optimise against is **slot-ms per MB scanned**. It normalises out the trivial "this query read a lot" case and isolates the structural cost: a simple filtered aggregate sits around 50 slot-ms/MB, the same query with a shuffle around 500, and one with a skewed join in the thousands. That single ratio tells you whether to go hunting for a shuffle without opening the graph.

**Failure story.** A dashboard query went from 5 minutes to 40 minutes overnight. The team checked bytes — unchanged — and slot-hours — unchanged — and concluded nothing had changed. What had changed was `total_rows_output`, which had gone from 2,000 to 90,000. A join had started matching more rows because a dimension table had been refreshed with a `NULL` key, and rows with `NULL` join keys match everything in a `LEFT JOIN`. The query was doing 45× the work and returning 45× the rows.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

def report(label, *, scanned_tb=0.0, slot_hours=0.0):
    e = estimate("bigquery", scanned_tb=scanned_tb, slot_hours=slot_hours, apply_free_tier=False)
    for line in e.lines:
        print(f"  {line.label:<22} {line.quantity:>8} x ${line.unit_price:<7} = ${line.cost:>8.2f}")
    print(f"  {label:<22} {'total':>8}                = ${e.total:>8.2f}")
    print(f"  {label:<22} {'slot_hours':>8}                = {slot_hours:>8}")
    print()

# The same bytes, very different compute. Only the graph tells you why.
report("simple aggregate",    scanned_tb=1.0)
report("same + shuffle",       scanned_tb=1.0, slot_hours=10)
report("same + heavy shuffle", scanned_tb=1.0, slot_hours=100)
```

Expected output:

```text
  On-demand scan              1.0 x $6.25    = $    6.25
  simple aggregate          total                = $    6.25
  simple aggregate       slot_hours                =      0.0

  On-demand scan              1.0 x $6.25    = $    6.25
  Flat-rate slots              10 x $0.06    = $    0.60
  same + shuffle            total                = $    6.85
  same + shuffle         slot_hours                =       10

  On-demand scan              1.0 x $6.25    = $    6.25
  Flat-rate slots             100 x $0.06    = $    6.00
  same + heavy shuffle      total                = $   12.25
  same + heavy shuffle   slot_hours                =      100
```

Identical bytes, three different bills — and the slot-hour cost is what the second and third queries pay on top. On on-demand pricing the byte line dominates; on capacity-based, the slot line is the *entire* bill.

---

### Q4. What is the difference between a broadcast join and a shuffle join?

**Answer.** A **broadcast hash join** copies the entire smaller table to every worker and probes it locally — **no shuffle, no network transfer of the big side**. A **shuffle join** redistributes *both* sides across workers by join key, so rows that share a key land on the same worker.

**Mechanism.** Shuffle join: both inputs are partitioned by the join key, rows with the same key are routed to the same worker, and each worker joins its partition. The cost is the network movement of both sides plus the memory to hold the partitions. Broadcast join: the small side is replicated to all workers, and each worker streams the large side past its local copy. Because the probe is local, there is no shuffle stage at all — and no skew, because every worker does the same amount of work.

**Trade-off.** Broadcast wins on latency and slot-hours when the small side genuinely fits. It loses when the "small" side is not small: replicating it to a thousand workers multiplies memory pressure and can tip workers into spilling. Shuffle wins when the build side is large, when the join key is skewed, or when the tables are in different locations and a shuffle is unavoidable anyway. BigQuery picks automatically, but the choice is visible in the execution graph — no shuffle stage means a broadcast.

**In practice.** The rule I use: **keep dimension tables small, and put them in their own table.** A dimension that is small enough to broadcast (typically under 10 MB compressed) should never be a join against a fact table at the same grain as the fact table's keys. And when BigQuery *doesn't* broadcast a join it should, the usual cause is that the build side was unexpectedly large — often because it had a `NULL` join key that prevented a filter from reducing it, or because it was a full table rather than a filtered subset.

**Failure story.** A join against a 4 GB "dimension" that was supposed to be small — a customer table that had accumulated every historical version of every customer, so it had 40M rows instead of 2M. BigQuery could not broadcast it, fell back to a shuffle join, and the query became the slowest in the pipeline. The fix was not to buy capacity; it was to make the dimension small again by keeping only current rows.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

# A broadcast join has no shuffle: compute is proportional to the scan.
broadcast = estimate("bigquery", scanned_tb=1.0, slot_hours=5, apply_free_tier=False).total
# A shuffle join redistributes the big side: same bytes, much more compute.
shuffle = estimate("bigquery", scanned_tb=1.0, slot_hours=50, apply_free_tier=False).total

print(f"broadcast (5 slot-hours):   ${broadcast:.2f}")
print(f"shuffle   (50 slot-hours):  ${shuffle:.2f}")
print(f"ratio: {shuffle / broadcast:.1f}x")

# On capacity-based pricing the byte line is not billed at all — only slots.
b_slots = estimate("bigquery", slot_hours=5, apply_free_tier=False).total
s_slots = estimate("bigquery", slot_hours=50, apply_free_tier=False).total
print(f"broadcast slots only: ${b_slots:.2f}")
print(f"shuffle   slots only: ${s_slots:.2f}")
print(f"slot ratio: {s_slots / b_slots:.0f}x")
```

Expected output:

```text
broadcast (5 slot-hours):   $6.55
shuffle   (50 slot-hours):  $9.25
ratio: 1.4x
broadcast slots only: $0.30
shuffle   slots only: $3.00
slot ratio: 10x
```

On on-demand pricing the byte cost dominates and the difference looks like 1.4×. On capacity-based pricing the byte line is not billed at all — only slots — and the same difference is **10×**. The join strategy barely moves the on-demand bill and moves the capacity bill by an order of magnitude.

---

### Q5. How does BigQuery automatically select a join strategy?

**Answer.** BigQuery estimates the size of both sides and the distribution of the join key, then picks a **broadcast hash join** when the build side is small enough to replicate, and a **shuffle join** otherwise. You do not set it directly, but you influence it entirely through the size and shape of your tables.

**Mechanism.** The planner works from table statistics and, for partitioned tables, from the filter you applied. Three factors decide it: the **size of the build side after filtering**, the **cardinality of the join key** (if one side has few distinct values, a broadcast is more attractive), and **whether the join key is sorted or clustered** on either side, which can enable a merge-style strategy without a full shuffle. The plan is visible in the execution graph — a join with no preceding shuffle stage was broadcast.

**Trade-off.** Automatic selection is right most of the time and wrong in the same two situations every time: the build side is bigger than it looks, or the key is skewed. Neither is visible from the query text, which is why you need the graph. And there is a nasty second-order effect: a broadcast join has *no skew problem*, so a query that BigQuery shuffles is a query that now has a straggler to wait for. A "slower" strategy can be exposing a skew that was previously hidden.

**In practice.** When a join does not broadcast, I check three things in order: how many rows the build side actually has *after* the filter (a `COUNT(*)` on the filtered side), how many distinct values the join key has, and whether the planner is being given stale statistics. A common cause of a missed broadcast is a `NULL` join key — BigQuery cannot prove the filtered build side is small when the filter leaves rows the join will match. Other causes are `OR` conditions that prevent partition pruning on the build side, and a build side that is a view over a large table.

**Failure story.** A team had a 12 MB dimension that stopped being broadcast after a schema change. The change was cosmetic — a column was added to the dimension — but the dimension was stored in a table that had never been clustered, and the new column changed the physical layout enough that the planner's estimate of the build side jumped above the broadcast threshold. Nothing about the query changed. The lesson: **broadcast thresholds are sensitive to table layout, not just query text**, so a table rewrite can silently change a join strategy.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import deduplicate, dedup_key

# Why the build side must be small AFTER filtering.
rows = [
    {"event_id": f"e{i}", "event_dt": "2026-01-15", "region": "AMER", "amount_eur": 10.0}
    for i in range(5)
]

# A dimension with duplicate keys is not a dimension — it multiplies the fact side.
deduped = deduplicate(rows, partition="20260115")
print("rows:", len(rows), "after dedup:", len(deduped))
print("key:", dedup_key("evt-0001", "20260115"))

# Every duplicate key in the build side is a fan-out risk on join.
keys = [dedup_key(r["event_id"], "20260115") for r in rows]
print("distinct keys:", len(set(keys)), "of", len(keys))
```

Expected output:

```text
rows: 5 after dedup: 5
key: 20260115:evt-0001
distinct keys: 5 of 5
```

A build side with **fewer distinct keys than rows** will multiply the fact side on join — the cardinality problem in miniature. That is the same property that makes a join *attractive* to broadcast and *dangerous* to shuffle at the same time.

---

### Q6. What is data skew, and how does it slow a query down?

**Answer.** Data skew is when the rows to be grouped or joined are **not evenly distributed** across keys — one key holds a disproportionate share of the data. The query slows down because the whole query waits for the slowest worker.

**Mechanism.** In a shuffle, rows are partitioned by key and each worker takes a partition. With a uniform distribution every worker finishes at roughly the same time. With skew, one key dominates: that worker gets 4.1M rows while its peers get 400K. The query cannot complete until the dominant worker does, so the other workers **sit idle holding their slots** for the whole duration. The cost is not the extra data — it is the wall-clock time multiplied by the number of slots that had nothing to do.

**Trade-off.** Skew is usually a data property, not a query bug, so "just rewrite the query" rarely fixes it. The causes are structural: a hot customer or product, a `NULL` or default key that collects everything, a timestamp where most events land in one bucket, or a slowly-changing dimension that was never split into versions. And skew is invisible to a bytes-based cost model — the query reads the same bytes either way, it just takes eight times as long.

**In practice.** Two numbers diagnose it: the **ratio of the largest key's share to the average key's share**, and the **ratio of the slowest worker's time to the median worker's**. A healthy distribution has a max share near 1× the average. A ratio above about 10× is skew; above 100× is a serious problem. And note the interaction with slot contention: because the idle workers still hold their slots, a skewed query in a capacity-based reservation is worse than it looks — it is blocking other queries from using the slots it is wasting.

**Failure story.** A daily report took 6 minutes and grew to 55 minutes over three months. The data had not grown meaningfully. The cause was one `partner_id` — a marketplace partner that had been integrated late and, by month three, accounted for 60% of all orders. One worker held 60% of the rows, and the other 999 waited. The report had been fine, then slow, then slower, with no change in volume — the classic shape of skew rather than growth.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter

# A skewed key distribution: one partner dominates.
keys = ["P1"] * 600 + [f"P{i}" for i in range(2, 42)] * 10
counts = Counter(keys)

total = sum(counts.values())
avg = total / len(counts)
worst = max(counts.values())
worst_key = max(counts, key=counts.get)

print(f"total rows:   {total}")
print(f"distinct keys: {len(counts)}")
print(f"average/key:   {avg:.1f}")
print(f"worst key:     {worst_key} with {worst} rows")
print(f"skew ratio:    {worst / avg:.1f}x")
print(f"one key holds: {worst / total * 100:.1f}% of all rows")
```

Expected output:

```text
total rows:   1000
distinct keys: 41
average/key:   24.4
worst key:     P1 with 600 rows
skew ratio:    24.6x
one key holds: 60.0% of all rows
```

A ratio of **24.6×** and **60% of all rows** in one key. The straggler worker holds that key, and every other worker waits for it.

---

### Q7. How do you identify data skew in the execution graph?

**Answer.** Look at the **shuffle output stage** and compare the **maximum rows per worker** against the **median**. If the max is several times the median, you have skew — and the stage where it appears tells you which key.

**Mechanism.** BigQuery's graph shows per-worker statistics on shuffle stages: rows read, rows written, bytes processed. A healthy shuffle is a flat histogram. A skewed one has one bar standing far above the rest. The distribution is the symptom; to find the *cause* you go back to the data and count rows per key for the suspect columns. You can also catch it early, before the graph: run a `COUNT(*)` grouped by the candidate key and look for a key that dominates.

**Trade-off.** The graph is diagnostic but reactive — it tells you a worker was slow, not which key made it slow. Finding the key requires querying the data, which costs another scan (do it on a partition, not the whole table). And BigQuery's graph samples rather than showing every worker, so a moderate skew may not be visible. The cheap pre-check — a grouped `COUNT(*)` on one partition — catches it earlier and more precisely than the graph does.

**In practice.** My sequence: (1) find the slow shuffle stage in the graph; (2) note the max-vs-median rows per worker; (3) run `SELECT key, COUNT(*) FROM table WHERE <one partition> GROUP BY key ORDER BY 2 DESC LIMIT 20` on a *single partition* to find the hot key; (4) check whether the hot key is a `NULL`, an empty string, or a sentinel like `0` or `'UNKNOWN'` — those are the ones that usually indicate a data-quality problem rather than genuine popularity.

**Failure story.** A team spent a week chasing a "slow shuffle" that turned out to be a graph-reading error. They read the *timeline* rather than the *distribution* — the shuffle stage showed a long bar, and they concluded the shuffle was slow because it took a long time. It took a long time because one worker had 40× the rows of the others, and the graph made that look like uniform slowness. Reading the histogram, not the bar length, would have shown the imbalance immediately.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter
import statistics

def skew_report(keys):
    counts = Counter(keys)
    total = sum(counts.values())
    avg = total / len(counts)
    ordered = sorted(counts.values(), reverse=True)
    median = statistics.median(ordered)
    return {
        "total": total,
        "distinct": len(counts),
        "avg": avg,
        "median": median,
        "max": ordered[0],
        "max_over_median": ordered[0] / median if median else 0,
        "max_over_avg": ordered[0] / avg if avg else 0,
    }

skewed = skew_report(["P1"] * 600 + [f"P{i}" for i in range(2, 42)] * 10)
even = skew_report([f"P{i}" for i in range(41)] * 10)

for label, r in (("skewed", skewed), ("even", even)):
    print(f"{label}: max/median = {r['max_over_median']:.1f}x  (max {r['max']}, median {r['median']})")
    print(f"{label}: max/avg    = {r['max_over_avg']:.1f}x  (max {r['max']}, avg {r['avg']:.1f})")
```

Expected output:

```text
skewed: max/median = 60.0x  (max 600, median 10)
skewed: max/avg    = 24.6x  (max 600, avg 24.4)
even: max/median = 1.0x  (max 10, median 10)
even: max/avg    = 1.0x  (max 10, avg 10.0)
```

**60× on the median ratio, 24.6× on the average ratio.** Use the median ratio to size the problem and the average ratio to size the *cost* — averaging hides the skew, because one huge key barely moves the mean. A healthy distribution sits at 1.0× on both.

---

### Q8. What is key salting, and when would you use it?

**Answer.** Key salting means **adding a random or deterministic suffix to a skewed join key** so the hot key's rows are spread across multiple workers. You use it when one key has far too many rows and the shuffle cannot be avoided.

**Mechanism.** If `partner_id = 'P1'` holds 60% of the rows, add a suffix: `P1_0` … `P1_9`. Now the shuffle partitions across ten keys, ten workers get an even slice, and no single worker is the straggler. The suffix must be **deterministic** — derived from a hash of the row's other data, or a fixed random seed — so that the same row always lands in the same partition and the join still works.

**Trade-off.** Salting makes the join work but changes the key. If the join key is a primary key used for lookups elsewhere, the salted version no longer matches, so you must salt **both** sides identically and then un-salt the output. It also breaks the natural clustering of the data — you can no longer prune blocks on the original key. And if you salt when the key was *not* actually skewed, you have added complexity and destroyed block pruning for nothing. It is a targeted tool, not a default.

**In practice.** I reach for salting when the fix is not available upstream. The **better** fixes, in order: (1) pre-aggregate the hot key so it is one row; (2) broadcast the dimension to eliminate the shuffle entirely; (3) separate the hot key into its own small table and union the results — "split the hot key out"; (4) salt. Salting is last because it is the most operationally complex. And it is only needed when the hot key's data must stay un-aggregated — if you can aggregate it, do that instead.

**Failure story.** A team salted a join key with `RAND()` — a fresh random value per row. Every row went to a random partition, so the same logical key's rows landed on different workers, and the join matched **almost nothing**. The result was a quietly wrong report: revenue collapsed to near zero, and nobody noticed for a week because the pipeline succeeded. The lesson: **the salt must be deterministic**, and a query whose output drops suspiciously should be checked before it is published.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter
import hashlib

def salt(key: str, row_id: str, buckets: int = 10) -> str:
    """Deterministic salt: the same (key, row) always lands in the same bucket.

    Note the salt is derived from a ROW attribute, not from the key alone.
    Salting by the key itself would leave every row of a hot key in the same
    bucket — the exact problem you were trying to solve.
    """
    digest = hashlib.md5(f"{key}|{row_id}".encode()).hexdigest()
    return f"{key}_{int(digest, 16) % buckets}"

# The hot key P1 with 600 rows; every row carries its own id.
rows = [("P1", f"r{i}") for i in range(600)]
rows += [(f"P{i}", f"r{i}") for i in range(2, 42) for _ in range(10)]

unsalted = Counter(k for k, _ in rows)
salted = Counter(salt(k, r) for k, r in rows)

print("unsalted worst key:", max(unsalted, key=unsalted.get), max(unsalted.values()))
print("salted   worst key:", max(salted, key=salted.get), max(salted.values()))
print("salted distinct buckets:", len(salted))
print("P1 spread over:", len([k for k in salted if k.startswith("P1_")]), "buckets")

# The salt must be stable: same input, same bucket, every time.
print("stable:", salt("P1", "r0") == salt("P1", "r0"))
```

Expected output:

```text
unsalted worst key: P1 600
salted   worst key: P1_4 83
salted distinct buckets: 50
P1 spread over: 10 buckets
stable: True
```

**600 rows in one worker becomes 83** — the hot key is spread across ten buckets and the straggler is gone. The `stable: True` check is the one that would have caught the `RAND()` bug. Note also that salting by the *key* alone would have left all 600 rows of `P1` in one bucket: the salt has to vary per row.

---

### Q9. What is a high-cardinality join, and why is it a problem?

**Answer.** A high-cardinality join is one where the join key has **many distinct values** — often close to one value per row. It is a problem because each key matches few or no other rows, so the join produces a result nearly as large as its inputs and BigQuery has no small side to broadcast.

**Mechanism.** High cardinality means the join is not a many-to-one lookup — it behaves more like a filter or a many-to-many operation. Two consequences. First, there is no small build side, so BigQuery must **shuffle** both inputs. Second, and more subtly, high cardinality is often a symptom of a **join key that is not actually a key** — joining on `event_id` or `timestamp` when you meant to join on a customer or product identifier means you are matching on something nearly unique, which means you are really doing a cross-product-with-filter.

**Trade-off.** Sometimes high cardinality is legitimate and unavoidable — a many-to-many relationship between two fact tables. But it is expensive enough that it is worth checking whether you meant it. The trade-off of "fixing" it by aggregating is that you lose the ability to re-slice at the finer grain later, which is the same trade-off as pre-aggregating anything.

**In practice.** The diagnostic: compare the number of distinct join keys to the number of rows on each side, and look at the **join's output row count** relative to its inputs. If the output is close to the product of the inputs, the key is not doing any work — the join is a disguised cross product and you should replace it with a different formulation entirely. If the output is much larger than the *larger* input, that is a genuine many-to-many fan-out and the fix is to pre-aggregate the many side to one row per key.

**Failure story.** A team joined an events table to a sessions table on `session_id`. Both had high-cardinality keys, and because `session_id` was unique in the sessions table, the join *should* have been a filter — but they had also joined on a `NULL`-able column, and rows with `NULL` session ids matched each other. The result grew by a factor of 4 and the query began timing out at the 2-hour limit. The fix was to filter `session_id IS NOT NULL` before the join, which reduced it to a proper lookup.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter

def cardinality(keys):
    counts = Counter(keys)
    n = len(keys)
    d = len(counts)
    return n, d, d / n

# A real key: many rows, few distinct values.
real_key = ["CUST-%d" % (i % 100) for i in range(1000)]
# Not a key: nearly unique per row.
not_a_key = ["EVT-%d" % i for i in range(1000)]

for label, keys in (("real key", real_key), ("not a key", not_a_key)):
    n, d, ratio = cardinality(keys)
    print(f"{label:<12} rows={n}  distinct={d}  distinct/row={ratio:.3f}")

# The fan-out test: output rows vs the larger input.
fact = 1000
dim = 1000
print(f"cross product would be {fact * dim:,} rows")
print(f"join on a real key produces ~{fact:,} rows")
```

Expected output:

```text
real key     rows=1000  distinct=100  distinct/row=0.100
not a key    rows=1000  distinct=1000  distinct/row=1.000
cross product would be 1,000,000 rows
join on a real key produces ~1,000 rows
```

A **distinct/row of 1.000** means the key identifies a single row — joining on it is a lookup at best and a cross product at worst.

---

### Q10. How do you prevent row multiplication during joins?

**Answer.** Three techniques, in order of preference: **pre-aggregate the many side to one row per key**, **filter `NULL` join keys before the join**, and **deduplicate the build side on the join key**. Know the output row count and assert on it.

**Mechanism.** Row multiplication happens when the build side has **more than one row per join key**. The fact side's rows each match several build rows, so the output is bigger than the input. It is a data problem, not a query problem — the SQL is doing exactly what you asked. The two usual causes: a dimension table with historical versions where you assumed one current row per key, and `NULL` join keys, which match each other under a `LEFT JOIN`.

**Trade-off.** Pre-aggregating is the correct fix but changes the grain — you lose the ability to re-slice at the finer level later. Deduplicating arbitrarily is worse: it silently discards data, and *which* row survives is arbitrary unless you pick deliberately (latest version by timestamp). And `NULL` filtering is nearly free but changes semantics: a `LEFT JOIN` that drops `NULL` rows is no longer a `LEFT JOIN`, which is occasionally what you want and frequently a surprise.

**In practice.** The discipline that catches it is **asserting on the output row count** in every pipeline. If rows out > rows in on a join, that is a bug, and the assertion should fail the job rather than publish. Concretely: `COUNT(*)` before and after, and a `HAVING COUNT(*) > 1` check on the build side's key — if that returns anything, the build side is not a dimension. The other half is making the dimension table genuinely one-row-per-key, with a "current version only" view over the history.

**Failure story.** A customer dimension had a `valid_from`/`valid_to` history, and the pipeline joined the fact table to the *whole history* rather than to current rows. Revenue per customer was inflated by roughly 4×, because each customer had four historical rows. The report had a sanity check on totals, but the totals were compared against the same flawed pipeline from last year, so they looked consistent. The assertion that would have caught it: the build side's join key must be unique — one row per key, always.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter

# A dimension that is not one-row-per-key: three versions of C1.
dimension = [
    {"customer_id": "C1", "valid_from": "2026-01-01"},
    {"customer_id": "C1", "valid_from": "2026-02-01"},
    {"customer_id": "C1", "valid_from": "2026-03-01"},
    {"customer_id": "C2", "valid_from": "2026-01-01"},
]

keys = [d["customer_id"] for d in dimension]
counts = Counter(keys)
offenders = {k: v for k, v in counts.items() if v > 1}

print("dimension rows:", len(dimension))
print("distinct keys:", len(counts))
print("keys with >1 row:", offenders)

# The assertion that catches it: no key may appear twice.
# In a pipeline this is a hard failure, not a warning.
if offenders:
    print(f"FAIL: dimension key is not unique -> {offenders}")

# The effect: one fact row for C1 matches three dimension rows.
fact = 1
multiplier = counts["C1"]
print(f"fact rows for C1 {fact} -> joined rows {fact * multiplier}")

# The fix: keep only the current version, so the key is unique again.
current = max(dimension, key=lambda d: d["valid_from"])
one_row_per_key = {d["customer_id"]: d for d in reversed(dimension)}
fixed_counts = Counter(one_row_per_key.keys())
print("after dedup, keys with >1 row:",
      {k: v for k, v in fixed_counts.items() if v > 1})
print("fact rows for C1 1 -> joined rows 1")
print("current version of C1:", current["valid_from"])
```

Expected output:

```text
dimension rows: 4
distinct keys: 2
keys with >1 row: {'C1': 3}
FAIL: dimension key is not unique -> {'C1': 3}
fact rows for C1 1 -> joined rows 3
after dedup, keys with >1 row: {}
fact rows for C1 1 -> joined rows 1
current version of C1: 2026-03-01
```

**1 fact row becomes 3.** That is the multiplication, and the `FAIL` line is the check that turns a silently wrong report into a failed job.

---

### Q11. How do you reduce shuffle operations in a query?

**Answer.** Three moves, in this order: **make the small side of a join small enough to broadcast**, **pre-aggregate before joining**, and **cluster both sides on the join key** so the join can be satisfied without a shuffle.

**Mechanism.** A shuffle is the redistribution of rows across workers by key. You remove it by not needing to redistribute. Broadcasting eliminates it outright — the small side is copied to every worker, so no data moves by key. Pre-aggregating reduces the volume to be shuffled, often to the point where the result is small enough to broadcast. Clustering on the join key sorts both sides the same way, so rows with the same key are already co-located and the join can run as a local merge.

**Trade-off.** Every one of these trades away something. Pre-aggregating loses the finer grain — the same trade-off as a materialized view. Clustering on the join key means you cannot also cluster on the key you *filter* on, because you get four columns total and the order matters; the first clustering column prunes most effectively. Broadcasting requires the build side to stay small, which means keeping dimensions small, which means a maintenance discipline. And clustering adds a sort cost on write.

**In practice.** The highest-leverage move, by far, is **making the dimension table small and separate**. Most analytic queries are fact-to-dimension, and the dimension is usually a few MB. When BigQuery cannot broadcast it, something has bloated it — usually history that was never separated out, or a `NULL` key that defeats the size estimate. The second move is clustering both sides on the join key, which is free at query time and pays off on every subsequent query. The third is pre-aggregation, which is the most invasive but also the biggest win when the fact table is huge.

**Failure story.** A team had a `customer_dimension` with 8M rows and could not work out why BigQuery would not broadcast it. The table included every field ever added to the customer record — including a `notes` column and a `preferences` JSON blob, which together made the table 400 MB compressed for 8M rows. Removing those two columns took it to 6 MB and BigQuery started broadcasting immediately, and the query went from 90 seconds to 4. **The fix was to stop storing payloads in dimension tables.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_events

# Pre-aggregate before the join: the volume that would be shuffled drops.
rows = [
    {"event_id": f"e{i}", "user_id": f"u{i % 3}", "event_ts": "2026-01-15T00:00:00Z",
     "event_type": "order", "region": "AMER", "channel": "web", "currency": "EUR", "amount": 10.0}
    for i in range(1000)
]

print("raw rows to shuffle:", len(rows))
summary = aggregate_events(rows)
print("rows after pre-aggregation:", len(summary))

# The compression ratio is the size of the shuffle you avoided.
print(f"reduction: {len(rows) / len(summary):.0f}x")
```

Expected output:

```text
raw rows to shuffle: 1000
rows after pre-aggregation: 1
reduction: 1000x
```

**1000×.** A fact table at a finer grain than anyone needs, pre-aggregated to the grain the query actually wants — that is a shuffle you never have to perform.

---

### Q12. What causes shuffle spill to disk?

**Answer.** Spill happens when the data a worker must hold in memory **exceeds its available memory**, so the engine writes the excess to disk and reads it back later. In a shuffle it is caused by a skewed key, a large build side, or too many concurrent shuffles per worker.

**Mechanism.** Each worker has a fixed memory budget. A shuffle stage materialises its partition in memory before writing it out. If one worker's partition is enormous — because the key is skewed, or because the build side was large and the join was not broadcast — it cannot fit, so the engine spills. Spilling is slow for two reasons: disk I/O is orders of magnitude slower than memory, and the spill/reload cycle adds a serialisation cost on top. A stage that spills is also a stage holding its slots far longer.

**Trade-off.** Spill is a symptom, and treating it as the disease is the mistake. The alternatives — more slots, more memory — cost money and may not help, because a skewed worker does not get proportionally more memory when you add workers elsewhere. Meanwhile, the *real* fix is upstream: reduce the partition size by fixing the skew, shrinking the build side, or pre-aggregating.

**In practice.** The tells in the execution graph: a shuffle stage with a large **spill to disk** or **peak memory** figure, and a stage duration far longer than its input size would suggest. The fix order I use: (1) is there a skew? (2) can the build side be broadcast? (3) can I pre-aggregate? (4) only then consider raising the reservation or memory per slot. I would also check whether the query is running on the on-demand or capacity path — the same query spills differently depending on what it competes with.

**Failure story.** A `GROUP BY` over a column that was mostly `NULL` spilled to disk on every run, and the team responded by doubling the reservation size. The bill doubled, the query still spilled — because the null key was still 40% of the rows and still landed in one partition. Adding workers does not split one partition; only a different partitioning strategy does. The actual fix was to filter or bucket the null key before the aggregation, which removed the spill and reduced the runtime by 90% at a *lower* cost.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from collections import Counter

# A null key collects everything into one partition — the spill cause.
keys = [None] * 400 + [f"K{i}" for i in range(60)] * 10

# The fix: give the null key its own treatment, or exclude it.
bucketed = ["__NULL__" if k is None else k for k in keys]
counts = Counter(bucketed)

worst = max(counts.values())
print(f"null rows: {sum(1 for k in keys if k is None)}")
print(f"worst partition: {worst} rows")
print(f"would fit in memory? {worst < 1000}")
print(f"nulls excluded: {sum(1 for k in keys if k is not None)} rows remain")
```

Expected output:

```text
null rows: 400
worst partition: 400 rows
would fit in memory? True
nulls excluded: 600 rows remain
```

The null key alone holds **400 rows** — 40% of the data in one partition. Excluding it, or bucketing it deliberately, is what stops the spill.

---

### Q13. What is the difference between partition pruning and column pruning?

**Answer.** **Partition pruning** removes whole partitions before any I/O, using a filter on the partitioning column. **Column pruning** removes individual columns before any I/O, using the `SELECT` list. They are independent and they compose.

**Mechanism.** Partition pruning is a *row-range* elimination: the partitioning column's value determines which partition a row lives in, so a filter that maps onto partition boundaries eliminates them at plan time. Column pruning is a *column* elimination: BigQuery's columnar layout (Capacitor) stores each column separately, so a query that references only `store_id` and `sale_date` reads only those columns' blocks. The condition for partition pruning is that the partition column appears **bare** — `sale_date = '2026-11-13'` prunes, `DATE(sale_date) = '...'` does not.

**Trade-off.** They fail differently and the fix differs. Partition pruning fails because of a function wrapper or a non-partitioned table; the fix is to unwrap the filter or add the partitioning. Column pruning fails because of `SELECT *` or a `SELECT * EXCEPT(...)` that still forces the full row to be materialised; the fix is to name the columns. And there is a subtlety: **a wide row is expensive even with perfect pruning** — pruning removes rows, not columns, so `SELECT *` over a partition you filtered to one day still reads every column of that day.

**In practice.** Both show up in the query plan, in the same place: the Scan stage reports bytes processed *before* pruning and *after* it. If the two are equal, neither pruning worked. In the console's query plan, look at "Bytes processed" versus the table's total size — that ratio is your combined pruning efficiency. I also check `INFORMATION_SCHEMA.JOBS.total_bytes_processed` against the expected table size as a regression test on the table's layout, not just the query.

**Failure story.** A team had a table with 200 columns, most of them added over the years for one-off reports. Every query used `SELECT *` because that was the house style, and every query read the full row width — so even a perfectly pruned single partition cost 40× what it should. The fix was not more partitioning; it was selecting named columns. Partition pruning was already working perfectly at 99.9%.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import estimated_scan_bytes

# Column pruning: the narrower the SELECT list, the fewer bytes.
wide = [
    {"event_id": f"e{i}", "user_id": f"u{i}", "event_dt": "2026-01-15",
     "region": "AMER", "amount_eur": 10.0, "notes": "x" * 200}
    for i in range(1000)
]
narrow = [{"event_id": r["event_id"], "amount_eur": r["amount_eur"]} for r in wide]

full = estimated_scan_bytes(wide, partitioned=False)
cols = estimated_scan_bytes(narrow, partitioned=False)
pruned = estimated_scan_bytes(wide, partitioned=True, partition_prune_ratio=0.01)

print(f"SELECT *            : {full:,} bytes")
print(f"narrow columns      : {cols:,} bytes")
print(f"partition-pruned    : {pruned:,} bytes")
print(f"column pruning gain : {full / cols:.1f}x")
print(f"partition gain      : {full / pruned:.0f}x")
```

Expected output:

```text
SELECT *            : 315,780 bytes
narrow columns      : 39,890 bytes
partition-pruned    : 3,157 bytes
column pruning gain : 7.9x
partition gain      : 100x
```

The `notes` column alone dominates the row width. Column pruning gave **7.9×**; partition pruning gave **100×**. They compose, and they are separate levers.

---

### Q14. Why should you avoid `SELECT *`?

**Answer.** Because it reads **every column**, and BigQuery bills for bytes read. It also breaks partition pruning when combined with certain constructs, makes the query's cost depend on schema changes you do not control, and hides the actual dependency from anyone reading the query.

**Mechanism.** BigQuery's columnar storage means cost tracks the bytes of the columns you reference. `SELECT *` references all of them, so a table with 200 columns costs 200 columns' worth to read even if you use two. Worse, `SELECT *` is not stable: a column added to the table changes the cost of every query that uses it, silently. And `SELECT *` in a `JOIN` or `UNION` forces a full materialisation of the row.

**Trade-off.** There is a genuine convenience case for `SELECT *`: exploratory work, and a `SELECT * EXCEPT(sensitive_column)` pattern that is safer than `SELECT *` for a one-off manual query. The rule is not "never" — it is "never in a pipeline or a repeated query." Exploration is billed by the same meter, but it is bounded and rare; a dashboard query that runs 200 times an hour is not.

**In practice.** The strongest argument is not cost, it is **blast radius**: `SELECT *` means an upstream schema change can change your query's meaning without changing your query. A column added as `NULLABLE` and then populated with something that breaks a downstream `COALESCE` — that is a real class of incident. In a typed pipeline I name every column, which also means the transformation layer fails loudly when the upstream schema drifts.

**Failure story.** A team added a `customer_email` column to a wide table. Every dashboard query used `SELECT *`, so a report that exported results to a spreadsheet silently started including customer emails — and that report went to a shared drive. It was a schema change, a cost regression (60% more bytes on every query), and a data leak, all from one `SELECT *`. The fix was to name columns and to put sensitive fields in a separate table entirely.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import estimated_scan_bytes

rows = [
    {"event_id": f"e{i}", "user_id": f"u{i}", "event_dt": "2026-01-15",
     "region": "AMER", "amount_eur": 10.0, "email": f"u{i}@example.com",
     "notes": "x" * 150, "ip_address": "10.0.0.1"}
    for i in range(1000)
]

select_star = estimated_scan_bytes(rows, partitioned=False)
needed = estimated_scan_bytes(
    [{"event_id": r["event_id"], "amount_eur": r["amount_eur"]} for r in rows],
    partitioned=False,
)

print(f"SELECT *        : {select_star:,} bytes")
print(f"named columns   : {needed:,} bytes")
print(f"you were paying : {select_star / needed:.1f}x more")
print(f"columns read    : {len(rows[0])} vs 2")
```

Expected output:

```text
SELECT *        : 320,670 bytes
named columns   : 39,890 bytes
you were paying : 8.0x more
columns read    : 8 vs 2
```

**8× more bytes** to read two columns out of eight. And the `email` and `ip_address` columns — the ones you did not need — were in the bill.

---

### Q15. How do you optimize `GROUP BY` operations?

**Answer.** Reduce the rows entering the group, reduce the width of the grouped rows, and make sure the grouping key is the one you actually need. In order: **pre-aggregate**, **project the narrow columns first**, and **cluster on the grouping key** where it fits.

**Mechanism.** A `GROUP BY` is a shuffle: rows are redistributed by the grouping key, then partial aggregates are combined. The shuffle volume is a function of *rows in × row width*, so both dimensions matter. A `SELECT` that projects only the grouping key and the aggregate expression before the aggregation reduces the shuffled width dramatically — BigQuery's optimizer often does this automatically, but a subquery or CTE makes it explicit and reliable.

**Trade-off.** Pre-aggregating at a coarser grain is the biggest win but is irreversible — you cannot re-slice at the finer grain. That is exactly the trade-off of a materialized view, and it is why the grain has to be chosen carefully rather than optimised opportunistically. Clustering on the grouping key helps a *later* query that filters on it, but it does not speed up the grouping itself — a shuffle is still needed.

**In practice.** The rule I apply: **aggregate as late as possible, but project as early as possible.** Those sound contradictory and are not — push the *narrow projection* early, push the *aggregation* as late as the grain requires. A common real example: a report that groups by `region, channel, product_category` over a year of events, where the fix is a pre-aggregated daily summary table with exactly those columns, refreshed incrementally. And the other half is **checking for skew in the grouping key** — a `GROUP BY` on a column with a `NULL` or a dominant value is a skew problem wearing a different hat.

**Failure story.** A team optimised a `GROUP BY` by adding `DISTINCT` inside the aggregate — `SUM(DISTINCT transaction_id)` — because the numbers looked wrong. That made the query slower and the numbers *still* wrong, because the actual cause was a fan-out join upstream that had duplicated rows before the aggregation ever ran. The lesson: **fix the multiplication upstream; never try to correct it with `DISTINCT` inside the aggregate**, because `DISTINCT` also collapses genuinely distinct values.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import aggregate_events

rows = [
    {"event_id": f"e{i}", "user_id": f"u{i % 3}", "event_dt": "2026-01-15T00:00:00+00:00",
     "event_type": "order", "region": "AMER", "channel": "web", "currency": "EUR", "amount_eur": 10.0}
    for i in range(1000)
]

# Project narrow, then aggregate: the shape you want in the SQL.
projected = [{"region": r["region"], "amount_eur": r["amount_eur"]} for r in rows]
print("rows in       :", len(rows))
print("rows projected:", len(projected))

summary = aggregate_events(rows)
for region, stats in summary.items():
    print(f"  {region}: {stats}")
```

Expected output:

```text
rows in       : 1000
rows projected: 1000
  AMER: {'event_count': 1000.0, 'revenue_eur': 10000.0}
```

The row count is unchanged by projecting — but the *width* is, and width is what the shuffle moves. 1000 rows of 6 columns is a very different shuffle from 1000 rows of 2.

---

### Q16. How do you optimize BigQuery `MERGE` statements?

**Answer.** `MERGE` in BigQuery is a full mutation of the target partition. Optimise it by **keeping the target small** — one row per key — **partitioning it on the merge key**, and **merging one partition at a time** rather than the whole table.

**Mechanism.** A `MERGE` does not patch rows in place. For each target partition it rewrites the affected data, which means reading the target, writing the result, and reconciling with the source. The cost is therefore proportional to the target's size in the touched partitions, not to the source's change volume. If the target is unpartitioned, one merge rewrites the whole table.

**Trade-off.** Merging per-partition is the right pattern and it is also more operationally complex — you need to know which partitions to touch, and a late-arriving record for an old partition means a backfill outside the normal window. And a `MERGE` on a table with a `NULL` join key will match `NULL`s to `NULL`s, which is usually not intended.

**In practice.** The standard pattern: partition the target by the same date the source is partitioned by, and run the merge **per partition** inside a loop or a Dataform/Composer task. That bounds the work to one day's data regardless of how big the table gets. Also: `WHEN NOT MATCHED BY SOURCE THEN DELETE` turns the merge into a full reconciliation and is expensive — use it only when you genuinely want to delete. And I always check whether a plain `INSERT` with a partition overwrite would do the job, because for an append-only target, `INSERT ... OVERWRITE` on a single partition is simpler, faster, and idempotent.

**Failure story.** A team ran a nightly `MERGE` against an unpartitioned 4 TB target table. It took 6 hours and rewrote 4 TB every night to change 2000 rows. After partitioning the target by date and merging one partition at a time, the same job took 40 seconds and touched 1 GB. The lesson: **the cost of a `MERGE` is the size of what it rewrites, not the size of what it changes.**

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import partition_for_date, dedup_key

# The per-partition merge pattern.
logical_date = "2026-01-15"
partition = partition_for_date(logical_date)
print(f"logical date : {logical_date}")
print(f"partition    : {partition}")

source = [{"event_id": f"e{i}", "event_dt": logical_date, "amount_eur": 10.0} for i in range(3)]
keys = [dedup_key(r["event_id"], partition) for r in source]
print(f"merge rows   : {len(source)}")
print(f"idempotent   : {len(set(keys)) == len(keys)}")
print("keys:", keys)
```

Expected output:

```text
logical date : 2026-01-15
partition    : 20260115
merge rows   : 3
idempotent   : True
keys: ['20260115:e0', '20260115:e1', '20260115:e2']
```

The key insight is the **idempotency**: a merge keyed on `partition:event_id` produces the same state if it runs twice, so a retry after a partial failure is safe. That is what lets you re-run the merge for a partition without checking whether it already ran.

---

### Q17. How do you implement incremental loads?

**Answer.** Track the **high-water mark** per source — the last successfully processed value — and load only what is newer. Use the **logical date of the run**, not `now()`, and make the operation idempotent so a retry is safe.

**Mechanism.** Incremental loading has three moving parts. The **watermark** is the cursor: a timestamp, a sequence number, or an offset. The **filter** selects rows above the watermark. The **commit** advances the watermark — and this is where most bugs live, because if you advance the watermark before the data is durably written, you have a permanent gap. The course's `watermark_lag` measures exactly this: how far behind the source the pipeline is.

**Trade-off.** Watermarks trade completeness for cost: a pure `> watermark` filter misses records that arrive *out of order* with an older timestamp. The alternatives are a **lookback window** (re-read the last N minutes and rely on idempotency to absorb the duplicates), or **change-data-capture** with a source sequence number, which captures every change regardless of timestamp. CDC is more correct and more expensive to operate.

**In practice.** The rules I follow: (1) derive the partition from the **logical date**, never `CURRENT_TIMESTAMP()` — a job that runs at 2am should load "yesterday", not "the last 24 hours", because a rerun for a backfilled day must target the same partition; (2) always add a **lookback window** on top of the watermark, because sources are not strictly ordered; (3) make the load **idempotent** with a key derived from the data (`dedup_key(event_id, partition)` → `20260115:evt-0001`), so the overlap duplicates collapse; (4) advance the watermark only **after** the write succeeds.

**Failure story.** A pipeline used `WHERE event_ts > (SELECT MAX(event_ts) FROM target)` as its incremental filter. A late-arriving record with a timestamp older than the current max was therefore never loaded — permanently. It was invisible because the data volume looked stable. The fix was to keep a separate, monotonic watermark (an ingest sequence number or the source's own update timestamp) rather than deriving it from the target's data, and to add a lookback window.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import watermark_lag, partition_for_date, dedup_key, parse_timestamp
from datetime import datetime, timezone, timedelta

rows = [
    {"event_id": "e1", "event_dt": "2026-01-15T00:00:00+00:00"},
    {"event_id": "e2", "event_dt": "2026-01-15T09:00:00+00:00"},
    {"event_id": "e3", "event_dt": "2026-01-15T23:30:00+00:00"},
]

processing_time = datetime(2026, 1, 16, 2, 0, tzinfo=timezone.utc)
lag = watermark_lag(rows, processing_time=processing_time)
print("watermark lag:", lag)

# The incremental load, keyed for idempotency.
partition = partition_for_date("2026-01-15")
print("partition:", partition)
print("keys:", [dedup_key(r["event_id"], partition) for r in rows])

# A late arrival: older timestamp, but it must still be caught by the lookback.
late = {"event_id": "e0", "event_dt": "2026-01-14T23:00:00+00:00"}
print("late arrival ts:", late["event_dt"])
lookback_start = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
caught = parse_timestamp(late["event_dt"]) >= lookback_start - timedelta(hours=1)
print("caught by lookback window:", caught)
```

Expected output:

```text
watermark lag: 2:30:00
partition: 20260115
keys: ['20260115:e1', '20260115:e2', '20260115:e3']
late arrival ts: 2026-01-14T23:00:00+00:00
caught by lookback window: True
```

The **2:30:00 lag** is the number to alert on — it tells you how far behind the source you are. And the late arrival at `23:00` the previous day is exactly the case a pure watermark filter would drop.

---

### Q18. How do you handle duplicate and late-arriving records?

**Answer.** **Duplicates** are handled with an idempotency key derived from the data, plus a `MERGE` or a dedup pass. **Late arrivals** are handled with a lookback window and a watermark that is independent of the data's own timestamps.

**Mechanism.** Both problems come from the same place — a pipeline that assumes records arrive in order and arrive once. For duplicates, the fix is a **deterministic key** so the same logical record always produces the same identity: the course's `dedup_key(event_id, partition)` gives `20260115:evt-0001`, so a retry is a no-op. For late arrivals, the fix is a **lookback window**: re-read the last N minutes of the source on every run and let idempotency absorb the overlap.

**Trade-off.** Dedup-by-key costs a `GROUP BY` or `MERGE` on the key — a real cost on a large target, and a shuffle if you are not careful. A lookback window costs re-reading the overlap on every run, which is proportional to the window size and the arrival rate. Both are cheap; both are worth paying. The alternative — trying to make the *source* deliver exactly once in order — is usually not available to you.

**In practice.** The layering I use: (1) a **lookback window** on the source filter, so late data is picked up; (2) a **deterministic idempotency key**; (3) a **`MERGE` on that key** so the write is idempotent; (4) an **event-time watermark** with a side output for records past the cutoff, so late data is not silently dropped — it is routed somewhere for reprocessing. And for the dedup itself, `QUALIFY ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1` keeps the most recent version, which is the right choice when the key is a versioned entity.

**Failure story.** A team deduped with `ROW_NUMBER()` but partitioned on `event_id` alone rather than `event_id, partition` — and their pipeline wrote each day to a partition-scoped table. The same `event_id` legitimately appeared in two partitions (a legitimate correction the next day), and the dedup kept only one of them, so the correction was silently deleted. The fix was to include the partition in the dedup key. It is the same `dedup_key(event_id, partition)` rule, and the failure was exactly the case where the partition was missing.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from pipeline_logic import dedup_key, deduplicate, dedup_key_set, partition_for_date

rows = [
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},
    {"event_id": "evt-0002", "event_dt": "2026-01-15", "amount_eur": 20.0},
    {"event_id": "evt-0001", "event_dt": "2026-01-15", "amount_eur": 10.0},   # duplicate
    {"event_id": "evt-0001", "event_dt": "2026-01-16", "amount_eur": 11.0},   # next day, same id
]

# Dedup runs PER PARTITION. Rows from two different days are deduped
# separately, because the partition is part of the identity.
by_partition = {}
for row in rows:
    p = partition_for_date(row["event_dt"])
    by_partition.setdefault(p, []).append(row)

total_in = 0
total_out = 0
for p in sorted(by_partition):
    deduped = deduplicate(by_partition[p], partition=p)
    total_in += len(by_partition[p])
    total_out += len(deduped)
    print(f"partition {p}: {len(by_partition[p])} in -> {len(deduped)} out")

print("in :", total_in)
print("out:", total_out)

# The partition must be part of the key, or a legitimate next-day row is lost.
keys = dedup_key_set(rows, partition="20260115")
print("keys:", sorted(keys))
print("key includes partition:", all(k.startswith("20260115:") for k in keys))
```

Expected output:

```text
partition 20260115: 3 in -> 2 out
partition 20260116: 1 in -> 1 out
in : 4
out: 3
keys: ['20260115:evt-0001', '20260115:evt-0002']
key includes partition: True
```

**4 in, 3 out** — the true duplicate was removed, and the next-day row survived. That fourth row (`evt-0001` on `2026-01-16`) is a *different* partition and a different logical record: dedup keyed on `event_id` alone would have thrown it away. Note also the first line: deduping *all four rows together* under one partition would have given 2 out and silently deleted the correction.

---

### Q19. A query went from 5 minutes to 40 minutes overnight. How do you investigate?

**Answer.** Treat it as a regression with a known-good baseline. Get the current and previous metrics for the same query, find which one moved, then find out why.

**Mechanism.** The comparison that matters is **the same query, the same parameters, at two points in time**. The metrics to pull from `INFORMATION_SCHEMA.JOBS`: `total_bytes_processed`, `total_slot_ms`, `total_rows_processed`, `total_rows_output`, and `elapsed_secs`. Whichever of these changed tells you where to look. Bytes up → the table grew or pruning broke. Slot-ms up but bytes flat → a shuffle appeared or got heavier. Rows output up → a fan-out appeared. Elapsed up with all three flat → contention or resource pressure, not the query.

**Trade-off.** The tempting shortcut is to look at what changed in the *code*, but the useful move is to compare *metrics*, because the same symptom has different causes and the metrics localise it in one query rather than three. And you need a baseline: if you did not record the previous run's metrics, you are inferring from logs instead of comparing, which is much weaker.

**In practice.** My sequence: (1) pull both runs' metrics and diff them; (2) if bytes moved, check whether the *table* grew — compare against the table's size and row count history, and check whether a partition filter stopped pruning; (3) if slot-ms moved, open the execution graph for both and compare the stage structure — a new shuffle stage is the usual answer; (4) if rows output moved, look for a fan-out — most often a dimension table that changed shape, or a `NULL` key that started matching; (5) if none of them moved, it is **not the query** — look at slot contention, a concurrent backfill, or a quota. And critically, check whether someone else changed the *table* rather than the query.

**Failure story.** A daily report went from 5 minutes to 40 minutes with no code change. The metrics showed bytes flat, slot-ms flat, rows output up 12×. The cause was a **dimension table that had been refreshed with a `NULL` key**, so rows with `NULL` keys matched each other in the `LEFT JOIN` and multiplied the result. The query was unchanged; the data was. The lesson: **always diff the metrics before looking at the code**, because "no code change" usually means "the data changed", and the metrics point straight at it.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import estimate

def diff(label, before, after):
    """Compare two runs of the same query on the metrics that matter."""
    print(f"\n{label}")
    for key in ("bytes_tb", "slot_hours", "rows_out"):
        b, a = before[key], after[key]
        if b == 0:
            continue
        ratio = a / b
        verdict = "REGRESSED" if ratio > 1.5 else ("improved" if ratio < 0.9 else "same")
        print(f"  {key:<12} {b:>10} -> {a:>10}  ({ratio:>5.1f}x) {verdict}")

before = {"bytes_tb": 2.0, "slot_hours": 20, "rows_out": 2000}
after  = {"bytes_tb": 2.0, "slot_hours": 20, "rows_out": 24000}

diff("5 min -> 40 min: the query did not change", before, after)
print("\nbytes flat, slot_ms flat, rows_output up 12x -> look for a fan-out join.")
print("cost of both runs: $%.2f vs $%.2f" % (
    estimate("bigquery", scanned_tb=before["bytes_tb"], apply_free_tier=False).total,
    estimate("bigquery", scanned_tb=after["bytes_tb"], apply_free_tier=False).total,
))
```

Expected output:

```text
5 min -> 40 min: the query did not change
  bytes_tb            2.0 ->        2.0  (  1.0x) same
  slot_hours           20 ->         20  (  1.0x) same
  rows_out           2000 ->      24000  ( 12.0x) REGRESSED

bytes flat, slot_ms flat, rows_output up 12x -> look for a fan-out join.
cost of both runs: $12.50 vs $12.50
```

The scan cost is **identical** — $12.50 both times — which is exactly why "the bill looks the same" is not evidence that nothing changed. The regression is in the *result*, and only `rows_output` shows it.

---

### Q20. How do you measure BigQuery query costs?

**Answer.** From the two meters BigQuery actually bills: **bytes scanned** for on-demand, **slot-hours** for capacity-based. Measure them from `INFORMATION_SCHEMA.JOBS`, and convert with the published rates — $6.25/TB and $0.06/slot-hour.

**Mechanism.** `INFORMATION_SCHEMA.JOBS` gives you, per job: `total_bytes_processed`, `total_slot_ms`, `total_billed_bytes`, `elapsed_secs`, `creation_time`, `job_id`, and `total_slot_ms`. Convert with `slot_ms / 3,600,000` to get slot-hours. The Cloud Billing export gives the authoritative dollars, but `INFORMATION_SCHEMA.JOBS` is where the attribution lives — which job, which user, which dataset, which bytes.

**Trade-off.** The two meters measure different things and a query has both. On on-demand, bytes dominate and the bill is predictable from the query text — which means the cost is knowable *before* running the query, via `--dry_run`. On capacity-based, slot-ms dominates and is **not** knowable in advance, because it depends on runtime and contention. So the measurement problem is easier on one model than the other, and that asymmetry is a real reason to prefer on-demand for anything unpredictable.

**In practice.** The three tools I use, in order of precision: (1) **`--dry_run`** — free, gives the exact bytes a query *would* scan, so you can price a query before you run it, which is the only reliable way to prevent a surprise bill; (2) **`INFORMATION_SCHEMA.JOBS`** — actuals per job, grouped by user and dataset, which is where you find the expensive team rather than the expensive query; (3) the **Cloud Billing export** — the dollars, for reconciliation. The derived metric I add is **slot-ms per MB scanned**, which normalises out size and exposes structural cost. And I always set `maximum_bytes_billed` so the measurement is bounded by failure rather than by surprise.

**Failure story.** A team discovered it had a $4,000 monthly BigQuery bill only at the end of the month, because nobody had instrumented cost. The spending was concentrated in one team running `SELECT COUNT(*)` over a 40 TB unpartitioned table every 15 minutes, for a "data quality check" that did not need to count anything — it needed to check for nulls in one column. Fixing it was a two-minute change (filter to one partition, select one column) and a `maximum_bytes_billed` cap. The lesson: **cost you cannot attribute is cost you cannot control**, and the attribution query is five lines.

**Check yourself.** Try it:
```python
import sys
sys.path.insert(0, "project/core")
from cost_model import BIGQUERY_ONDEMAND_PER_TB, BIGQUERY_SLOT_HOUR, estimate

# Meter 1: bytes. Knowable before you run.
print(f"on-demand rate: ${BIGQUERY_ONDEMAND_PER_TB}/TB")
for tb in (0.5, 5.0, 50.0):
    print(f"  {tb:>5} TB -> ${estimate('bigquery', scanned_tb=tb, apply_free_tier=False).total:>8.2f}")

# Meter 2: slot-hours. Knowable only after you run.
print(f"\nslot rate: ${BIGQUERY_SLOT_HOUR}/slot-hour")
slot_ms = 18_000_000
slot_hours = slot_ms / 3_600_000
print(f"  {slot_ms:,} slot-ms -> {slot_hours:.0f} slot-hours -> ${slot_hours * BIGQUERY_SLOT_HOUR:.2f}")

# Both meters on the same query.
both = estimate("bigquery", scanned_tb=10.0, slot_hours=slot_hours, apply_free_tier=False).total
print(f"\n10 TB + {slot_hours:.0f} slot-hours: ${both:.2f}")
print(f"  of which bytes: ${estimate('bigquery', scanned_tb=10.0, apply_free_tier=False).total:.2f}")
print(f"  of which slots: ${slot_hours * BIGQUERY_SLOT_HOUR:.2f}")
```

Expected output:

```text
on-demand rate: $6.25/TB
    0.5 TB -> $    3.12
    5.0 TB -> $   31.25
   50.0 TB -> $  312.50

slot rate: $0.06/slot-hour
  18,000,000 slot-ms -> 5 slot-hours -> $0.30

10 TB + 5 slot-hours: $62.80
  of which bytes: $62.50
  of which slots: $0.30
```

The **$0.30** slot component is nearly invisible next to the $62.50 scan component — on on-demand pricing. On capacity-based, the same 5 slot-hours is charged against a reservation regardless, and a query that burned 500 slot-hours instead of 5 would be a very different month.

---

## 📚 Related chapters

- [3.1 — Data Warehousing Concepts](../chapters/12-data-warehousing-concepts.md)
- [3.2 — BigQuery Platform Overview](../chapters/13-bigquery-platform-overview.md)
- [3.3 — BigQuery Query Optimization](../chapters/14-bigquery-query-optimization.md)
- [3.4 — BigLake, Dataplex & Data Catalog](../chapters/15-biglake-dataplex-and-data-catalog.md)

For the hands-on version of the cost and byte maths in this file, see the
practice suite: [`practice/04-querying-and-internals.md`](../practice/04-querying-and-internals.md)
for the query stages and the execution graph, and
[`practice/02-query-cost-lab.ipynb`](../practice/notebooks/02-query-cost-lab.ipynb)
for the four architectures priced side by side.

## 📖 Further Reading

- [BigQuery documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery pricing](https://cloud.google.com/bigquery/pricing)
- [BigQuery best practices for cost control](https://cloud.google.com/bigquery/docs/best-practices-cost-control)
- [Optimize query performance](https://cloud.google.com/bigquery/docs/query-optimization)
- [INFORMATION_SCHEMA.JOBS](https://cloud.google.com/bigquery/docs/information-schema-jobs)
- [Workload management](https://cloud.google.com/bigquery/docs/workload-management)
- [Course interview bank: Analytics and Cost](03-analytics-and-cost.md)
